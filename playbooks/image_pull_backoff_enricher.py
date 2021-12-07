import enum
from enum import Flag
from robusta.api import *


class ImagePullPackParams(BaseModel):
    rate_limit: int = 3600


def get_image_pull_backoff_container_statuses(status: PodStatus) -> [ContainerStatus]:
    return [
        container_status
        for container_status in status.containerStatuses
        if container_status.state.waiting is not None
        and container_status.state.waiting.reason == "ImagePullBackOff"
    ]


def decompose_flag(flag: Flag) -> List[Flag]:
    members, _ = enum._decompose(flag.__class__, flag._value_)
    return members


@action
def image_pull_backoff_reporter(event: PodEvent, action_params: ImagePullPackParams):
    # Extract pod. Terminate if not found
    pod = event.get_pod()
    if pod is None:
        return

    # Check if image pull backoffs occurred. Terminate if not
    image_pull_backoff_container_statuses = get_image_pull_backoff_container_statuses(pod.status)
    if len(image_pull_backoff_container_statuses) == 0:
        return

    # Extract pod name and namespace
    pod_name = pod.metadata.name
    namespace = pod.metadata.namespace

    # Perform a rate limit for this pod according to the rate_limit parameter
    if not RateLimiter.mark_and_test(
            "image_pull_backoff_reporter", namespace + ":" + pod_name, action_params.rate_limit
    ):
        return

    # Extract the error message and reason for the image pull back for every container with the ImagePullBackOff status.
    # Put all the relevant information into Markdown Blocks
    blocks: List[BaseBlock] = []
    investigator = ImagePullBackoffInvestigator(pod_name, namespace)
    for container_status in image_pull_backoff_container_statuses:
        investigation = investigator.investigate(container_status)

        if investigation is None:
            blocks.append(
                MarkdownBlock(
                    f"We cannot detect the reason for the ImagePullBackoff, as we failed failed to extract the image pull backoff error message "
                    f"for container {container_status.name} with image {container_status.image}. "
                    f"(Is your cluster using a container runtime that is other than docker and containerd?)"
                )
            )
            continue

        reason = investigation.reason
        error_message = investigation.error_message

        if reason != ImagePullBackoffReason.Unknown:
            reasons = decompose_flag(reason)
            if len(reasons) == 1:
                blocks.append(
                    MarkdownBlock(
                        f"Image pull error occurred for container **{container_status.name}** "
                        f"for the following reason: **{reason}**\n\n"
                        f"Error Message:\n{error_message}"
                    )
                )
            else:
                line_separated_reasons = "\n".join([f"**{r}**" for r in reasons])
                blocks.append(
                    MarkdownBlock(
                        f"Image pull error occurred for container **{container_status.name}** "
                        f"for one of the following reasons:\n"
                        f"{line_separated_reasons}\n\n"
                        f"Error Message:\n{error_message}"
                    )
                )
        else:
            blocks.append(
                MarkdownBlock(
                    f"Failed to extract reason for image pull error for container **{container_status.name}** "
                    f"for the following reason: error message not recognized\n\n"
                    f"Error message:\n{error_message}"
                )
            )

    # Create and return a finding with the calculated blocks
    finding = Finding(
        title=f"failed to pull at least one image in pod {pod_name} in namespace {namespace}",
        source=FindingSource.KUBERNETES_API_SERVER,
        aggregation_key="image_pull_backoff_reporter",
        subject=FindingSubject(
            pod_name, FindingSubjectType.TYPE_POD, namespace
        ),
    )
    finding.add_enrichment(blocks)
    event.add_finding(finding)


class ImagePullBackoffReason(Flag):
    Unknown = 0
    RepoDoesntExist = 1
    NotAuthorized = 2
    ImageDoesntExist = 4
    TagNotFound = 8


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
            "reason": ImagePullBackoffReason.RepoDoesntExist | ImagePullBackoffReason.ImageDoesntExist | ImagePullBackoffReason.TagNotFound
        },
        {
            "err_template": ('failed to pull and unpack image ".*?": failed to resolve reference ".*?": '
                             'pull access denied, repository does not exist or may require authorization: server message: '
                             'insufficient_scope: authorization failed'),
            "reason": ImagePullBackoffReason.NotAuthorized | ImagePullBackoffReason.ImageDoesntExist
        },
        {
            "err_template": ('failed to pull and unpack image ".*?": failed to resolve reference ".*?": '
                             'failed to authorize: failed to fetch anonymous token: unexpected status: 403 Forbidden'),
            "reason": ImagePullBackoffReason.NotAuthorized
        },

        # Docker
        {
            "err_template": ("Error response from daemon: pull access denied for .*?, "
                             "repository does not exist or may require 'docker login': denied: requested access to the resource is denied"),
            "reason": ImagePullBackoffReason.NotAuthorized | ImagePullBackoffReason.ImageDoesntExist
        },
        {
            "err_template": 'Error response from daemon: manifest for .*? not found: manifest unknown: manifest unknown',
            "reason": ImagePullBackoffReason.TagNotFound
        },
        {
            "err_template": ('Error response from daemon: Head ".*?": denied: '
                             'Permission "artifactregistry.repositories.downloadArtifacts" denied on resource ".*?" \\(or it may not exist\\)'),
            "reason": ImagePullBackoffReason.NotAuthorized
        },
        {
            "err_template": 'Error response from daemon: manifest for .*? not found: manifest unknown: Failed to fetch ".*?"',
            "reason": ImagePullBackoffReason.ImageDoesntExist | ImagePullBackoffReason.TagNotFound
        }
    ]

    def __init__(self, pod_name: str, namespace: str):
        self.pod_name = pod_name
        self.namespace = namespace

        self.pod_events: EventList = EventList.listNamespacedEvent(self.namespace, field_selector=f"involvedObject.name={self.pod_name}").obj

    def investigate(self, container_status: ContainerStatus) -> Optional[ImagePullOffInvestigation]:
        for pod_event in self.pod_events.items:
            error_message = self.get_kubelet_image_pull_error_from_event(pod_event, container_status.image)
            if error_message is None:
                continue

            reason = self.get_reason_from_kubelet_image_pull_error(error_message)

            return ImagePullOffInvestigation(error_message=error_message, reason=reason)

        return None

    @staticmethod
    def get_kubelet_image_pull_error_from_event(pod_event: Event, image_name: str) -> Optional[str]:
        if pod_event.type != "Warning":
            return None

        if pod_event.reason != "Failed":
            return None

        if pod_event.source.component != "kubelet":
            return None

        prefixes = [
            f"Failed to pull image \"{image_name}\": rpc error: code = Unknown desc = ",
            f"Failed to pull image \"{image_name}\": rpc error: code = NotFound desc = "
        ]

        for prefix in prefixes:
            if pod_event.message.startswith(prefix):
                return pod_event.message[len(prefix):]

        return None

    def get_reason_from_kubelet_image_pull_error(self, kubelet_image_pull_error: str) -> ImagePullBackoffReason:
        for config in self.configs:
            err_template = config["err_template"]
            reason = config["reason"]
            if re.fullmatch(err_template, kubelet_image_pull_error) is not None:
                return reason

        return ImagePullBackoffReason.Unknown
