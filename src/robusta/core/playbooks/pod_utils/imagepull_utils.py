import enum
import json
import logging
import re
from enum import Flag
from typing import List, Optional

from hikaru.model.rel_1_26 import ContainerStatus, Event, EventList, Pod, PodStatus

from robusta.core.reporting import BaseBlock, HeaderBlock, MarkdownBlock


class ImagePullBackoffReason(Flag):
    Unknown = 0
    RepoDoesntExist = 1
    NotAuthorized = 2
    ImageDoesntExist = 4
    TagNotFound = 8


def get_image_pull_backoff_container_statuses(status: PodStatus) -> List[ContainerStatus]:
    return [
        container_status
        for container_status in status.containerStatuses
        if container_status.state.waiting is not None
        and container_status.state.waiting.reason in ["ImagePullBackOff", "ErrImagePull"]
    ]


def decompose_flag(flag: Flag) -> List[Flag]:
    members, _ = enum._decompose(flag.__class__, flag._value_)
    return members


def get_image_pull_backoff_blocks(pod: Pod) -> Optional[List[BaseBlock]]:
    blocks: List[BaseBlock] = []
    pod_name = pod.metadata.name
    namespace = pod.metadata.namespace
    image_pull_backoff_container_statuses = get_image_pull_backoff_container_statuses(pod.status)
    investigator = ImagePullBackoffInvestigator(pod_name, namespace)
    for container_status in image_pull_backoff_container_statuses:
        investigation = investigator.investigate(container_status)

        blocks.extend(
            [
                HeaderBlock(f"ImagePullBackOff in container {container_status.name}"),
                MarkdownBlock(f"*Image:* {container_status.image}"),
            ]
        )

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
            reasons = decompose_flag(reason)

            if len(reasons) == 1:
                blocks.extend(
                    [
                        MarkdownBlock(f"*Reason:* {reason}"),
                    ]
                )
            else:
                line_separated_reasons = "\n".join([f"{r}" for r in reasons])
                blocks.extend(
                    [
                        MarkdownBlock(f"*Possible reasons:*\n{line_separated_reasons}"),
                    ]
                )
        else:
            blocks.append(MarkdownBlock(f"*Error message:* {container_status.name}:\n{error_message}"))
    return blocks


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
            "err_template": 'failed to pull and unpack image ".*?": failed to resolve reference ".*?": .*?: not found',
            "reason": ImagePullBackoffReason.RepoDoesntExist
            | ImagePullBackoffReason.ImageDoesntExist
            | ImagePullBackoffReason.TagNotFound,
        },
        {
            "err_template": (
                'failed to pull and unpack image ".*?": failed to resolve reference ".*?": '
                "pull access denied, repository does not exist or may require authorization: server message: "
                "insufficient_scope: authorization failed"
            ),
            "reason": ImagePullBackoffReason.NotAuthorized | ImagePullBackoffReason.ImageDoesntExist,
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
            "reason": ImagePullBackoffReason.NotAuthorized | ImagePullBackoffReason.ImageDoesntExist,
        },
        {
            "err_template": "Error response from daemon: manifest for .*? not found: manifest unknown: manifest unknown",
            "reason": ImagePullBackoffReason.TagNotFound,
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
            "reason": ImagePullBackoffReason.ImageDoesntExist | ImagePullBackoffReason.TagNotFound,
        },
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
