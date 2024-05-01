import enum
import json
import logging
import re
from enum import Flag
from typing import List, Optional, Tuple

from hikaru.model.rel_1_26 import ContainerStatus, Event, EventList, Pod, PodStatus

from robusta.core.reporting import BaseBlock, MarkdownBlock, TableBlock
from robusta.core.reporting.base import EnrichmentType, Enrichment
from robusta.core.reporting.blocks import TableBlockFormat


class ImagePullBackoffReason(Flag):
    Unknown = 0
    RepoDoesntExist = 1
    NotAuthorized = 2
    Timeout = 16


def get_image_pull_backoff_container_statuses(status: PodStatus) -> List[ContainerStatus]:
    return [
        container_status
        for container_status in status.containerStatuses
        if container_status.state.waiting is not None
        and container_status.state.waiting.reason in ["ImagePullBackOff", "ErrImagePull"]
    ]


def get_pod_issue_message_and_reason(pod: Pod) -> Tuple[Optional[str], Optional[str]]:
    # Works/should work only or KubeContainerWaiting and KubePodNotReady
    # Note: in line with the old code in pod_issue_investigator, we only get the message for
    # the first of possibly many misbehaving containers.
    if pod.status.containerStatuses:
        if pod.status.containerStatuses[0].state.waiting:
            reason = pod.status.containerStatuses[0].state.waiting.reason
            if reason is None:
                reason = "unknown"
            return (
                pod.status.containerStatuses[0].state.waiting.message,
                reason,
            )
    return None, None


def get_image_pull_backoff_enrichment(pod: Pod) -> Enrichment:
    error_blocks: List[BaseBlock] = []
    image_pull_table_blocks: List[BaseBlock] = []
    pod_name = pod.metadata.name
    namespace = pod.metadata.namespace
    image_pull_backoff_container_statuses = get_image_pull_backoff_container_statuses(pod.status)
    investigator = ImagePullBackoffInvestigator(pod_name, namespace)

    for container_status in image_pull_backoff_container_statuses:
        image_issue_rows: List[List[str]] = \
            [["Container", container_status.name], ["Image", container_status.image]]

        investigation = investigator.investigate(container_status)

        # TODO: this happens when there is a backoff but the original events containing the actual error message are already gone
        # and all that remains is a backoff event without a detailed error message - maybe we should identify that case and
        # print "backoff - too many failed image pulls" or something like that
        if investigation is None:
            events = [
                {
                    "type": event.type,
                    "reason": event.reason,
                    "source.component": event.deprecatedSource.component,
                    "message": event.note,
                }
                for event in investigator.pod_events.items
            ]
            logging.info(
                "could not find the image pull error in the kubernetes events. All the relevant events follow, so we can figure out why"
            )
            logging.info(json.dumps(events, indent=4))
            continue

        reason = investigation.reason
        error_message = investigation.error_message
        if reason != ImagePullBackoffReason.Unknown:
            backoff_reason = __imagepull_backoff_reason_to_fix(reason=reason)

            if backoff_reason:
                reason_text, fix = backoff_reason
                image_issue_rows.append(["Reason", reason_text])
                image_issue_rows.append(["Fix", fix])

        else:
            error_blocks.append(MarkdownBlock(f"*Error message:* {container_status.name}:\n{error_message}"))

        image_pull_table_blocks.append(TableBlock(
            [[k, v] for (k, v) in image_issue_rows],
            ["label", "value"],
            table_format=TableBlockFormat.vertical,
        ))

    image_pull_table_blocks.extend(error_blocks)

    return Enrichment(
        enrichment_type=EnrichmentType.image_pull_backoff_info,
        blocks=image_pull_table_blocks,
        title="Container ImagePullBackoff Information")


def __imagepull_backoff_reason_to_fix(reason: ImagePullBackoffReason) -> Optional[Tuple[str, str]]:
    if reason == ImagePullBackoffReason.RepoDoesntExist:
        return "Image not found", "Make sure the image repository, image name and image tag are correct."
    if reason == ImagePullBackoffReason.NotAuthorized:
        return "Unauthorized", 'The repo is access protected. Make sure to configure the correct image pull secrets: https://kubernetes.io/docs/tasks/configure-pod-container/pull-image-private-registry'
    if reason == ImagePullBackoffReason.Timeout:
        return "Timeout", 'If this does not resolved after a few minutes, make sure the image repository is responding.'

    return None


class ImagePullOffInvestigation:
    error_message: str
    reason: ImagePullBackoffReason

    def __init__(self, error_message: str, reason: ImagePullBackoffReason):
        self.error_message = error_message
        self.reason = reason


class ImagePullBackoffInvestigator:
    configs = [
        # Containerd
        {
            "err_template": r'failed to pull and unpack image ".*?": failed to resolve reference ".*?": .*?(no such host|not found)',
            "reason": ImagePullBackoffReason.RepoDoesntExist,
        },
        {
            "err_template": (
                'failed to pull and unpack image ".*?": failed to resolve reference ".*?": '
                "pull access denied, repository does not exist or may require authorization: server message: "
                "insufficient_scope: authorization failed"
            ),
            "reason": ImagePullBackoffReason.NotAuthorized,
        },
        {
            "err_template": (
                'failed to pull and unpack image ".*?": failed to resolve reference ".*?": '
                "failed to authorize: failed to fetch anonymous token: unexpected status: 403 Forbidden"
            ),
            "reason": ImagePullBackoffReason.NotAuthorized,
        },
        # Docker
        {
            "err_template": (
                "Error response from daemon: pull access denied for .*?, "
                "repository does not exist or may require 'docker login': denied: requested access to the resource is denied"
            ),
            "reason": ImagePullBackoffReason.NotAuthorized,
        },
        {
            "err_template": "Error response from daemon: manifest for .*? not found: manifest unknown: manifest unknown",
            "reason": ImagePullBackoffReason.RepoDoesntExist,
        },
        {
            "err_template": (
                'Error response from daemon: Head ".*?": denied: '
                'Permission "artifactregistry.repositories.downloadArtifacts" denied on resource ".*?" \\(or it may not exist\\)'
            ),
            "reason": ImagePullBackoffReason.NotAuthorized,
        },
        {
            "err_template": 'Error response from daemon: manifest for .*? not found: manifest unknown: Failed to fetch ".*?"',
            "reason": ImagePullBackoffReason.RepoDoesntExist,
        },
        {
            "err_template": r'.*Timeout exceeded.*',
            "reason": ImagePullBackoffReason.Timeout,  # Using the Timeout reason
        }
    ]

    def __init__(self, pod_name: str, namespace: str):
        self.pod_name = pod_name
        self.namespace = namespace

        self.pod_events: EventList = EventList.listNamespacedEvent(
            self.namespace, field_selector=f"regarding.name={self.pod_name}"
        ).obj

    def investigate(self, container_status: ContainerStatus) -> Optional[ImagePullOffInvestigation]:
        for pod_event in self.pod_events.items:
            error_message = self.get_kubelet_image_pull_error_from_event(pod_event, container_status.image)
            logging.debug(f"for {pod_event} got message: {error_message}")
            if error_message is None:
                continue

            reason = self.get_reason_from_kubelet_image_pull_error(error_message)
            logging.debug(f"reason is: {reason}")

            return ImagePullOffInvestigation(error_message=error_message, reason=reason)

        return None

    @staticmethod
    def get_kubelet_image_pull_error_from_event(pod_event: Event, image_name: str) -> Optional[str]:
        if pod_event.type != "Warning":
            return None

        if pod_event.reason != "Failed":
            return None

        if pod_event.deprecatedSource.component != "kubelet":
            return None

        prefixes = [
            f'Failed to pull image "{image_name}": rpc error: code = Unknown desc = ',
            f'Failed to pull image "{image_name}": rpc error: code = NotFound desc = ',
        ]

        for prefix in prefixes:
            if pod_event.note.startswith(prefix):
                return pod_event.note[len(prefix) :]

        return None

    def get_reason_from_kubelet_image_pull_error(self, kubelet_image_pull_error: str) -> ImagePullBackoffReason:
        for config in self.configs:
            err_template = config["err_template"]
            reason = config["reason"]
            if re.fullmatch(err_template, kubelet_image_pull_error) is not None:
                return reason

        return ImagePullBackoffReason.Unknown
