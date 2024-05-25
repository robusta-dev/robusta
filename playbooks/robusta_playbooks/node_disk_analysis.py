import logging
import re
from typing import Dict, List

import humanize
from hikaru.model.rel_1_26 import EnvVar, EnvVarSource, ObjectFieldSelector, PodList

from robusta.api import (
    DISK_TOOLS_IMAGE,
    IMAGE_REGISTRY,
    BaseBlock,
    MarkdownBlock,
    NodeEvent,
    PodRunningParams,
    RobustaPod,
    TableBlock,
    action,
)
from robusta.utils.parsing import load_json


class DiskAnalyzerParams(PodRunningParams):
    show_pods: bool = True
    show_containers: bool = False


@action
def node_disk_analyzer(event: NodeEvent, params: DiskAnalyzerParams):
    """
    Provides relevant disk information for troubleshooting disk issues.
    Currently, the following information is provided by default:
        * The total disk space used by pods, and the total disk space used by the node for other purposes
        * Disk usage of pods, sorted from highest to lowest

    You can change the parameters to show additional data:
        * Disk usage of containers, sorted (separately for every pod) from highest to lowest
    """
    node = event.get_node()
    if not node:
        logging.error(f"cannot run node disk analysis on event with no node object: {event}")
        return

    blocks: List[BaseBlock] = []

    # map pod names and namespaces by pod uid, and container names by container id
    node_pods: PodList = PodList.listPodForAllNamespaces(field_selector=f"spec.nodeName={node.metadata.name}").obj

    pod_uid_to_name: Dict[str, str] = {}
    pod_uid_to_namespace: Dict[str, str] = {}
    container_id_to_name: Dict[str, str] = {}

    for pod in node_pods.items:
        pod_uid_to_name[pod.metadata.uid] = pod.metadata.name
        pod_uid_to_namespace[pod.metadata.uid] = pod.metadata.namespace

        # If the "kubernetes.io/config.hash" annotation exists, it is used as the UID. Therefore, if it is present, we consider the config hash to be a pod uid too.
        # See https://github.com/weaveworks/scope/issues/2931 and https://github.com/weaveworks/scope/blob/v1.6.5/probe/kubernetes/pod.go#L47 for more information.
        if pod.metadata.annotations is not None and "kubernetes.io/config.hash" in pod.metadata.annotations:
            pod_uid_to_name[pod.metadata.annotations["kubernetes.io/config.hash"]] = pod.metadata.name
            pod_uid_to_namespace[pod.metadata.annotations["kubernetes.io/config.hash"]] = pod.metadata.namespace

        for container_status in pod.status.containerStatuses:
            # containers with ImagePullBackOff will have no containerID and throw an exception in regex
            if container_status.containerID:
                container_id = re.match(".*//(.*)$", container_status.containerID).group(1)  # type: ignore
                container_id_to_name[container_id] = container_status.name

    # run disk-tools on node and parse its json output
    disk_info_str = RobustaPod.run_debugger_pod(
        node.metadata.name,
        pod_image=f"{IMAGE_REGISTRY}/{DISK_TOOLS_IMAGE}",
        env=[
            EnvVar(
                name="CURRENT_POD_UID",
                valueFrom=EnvVarSource(fieldRef=ObjectFieldSelector(fieldPath="metadata.uid")),
            )
        ],
        mount_host_root=True,
        custom_annotations=params.custom_annotations,
    )
    # The code for the disk-tools image can be found in https://github.com/robusta-dev/disk-tools
    # Please refer to this code in order to see the structure of the json that is returned

    disk_info = load_json(disk_info_str)
    pods_distribution = disk_info["pods_disk_info"]["pods_distribution"]

    # calculate disk info block
    disk_stats = disk_info["disk_stats"]
    used_bytes = disk_stats["used"]
    total_bytes = disk_stats["total"]
    total_pods_disk_space_in_bytes = 0
    for p in pods_distribution:
        for c in p["containers"]:
            total_pods_disk_space_in_bytes += c["disk_size"]

    used = humanize.naturalsize(used_bytes, binary=True)
    total = humanize.naturalsize(total_bytes, binary=True)
    used_percentage = round(used_bytes / total_bytes * 100, 2)
    total_pod_disk_space = humanize.naturalsize(total_pods_disk_space_in_bytes, binary=True)
    other_disk_space = humanize.naturalsize(used_bytes - total_pods_disk_space_in_bytes, binary=True)
    blocks.append(
        MarkdownBlock(
            f"Disk analysis for node {node.metadata.name} follows.\n"
            f"The used disk space is currently at {used} out of {total} ({used_percentage}%).\n"
            f"Of this space, {total_pod_disk_space} is used by pods "
            f"and the rest ({other_disk_space}) is consumed by the node."
        )
    )

    # calculate pod-level disk distribution block
    if params.show_pods:
        pod_distribution_headers = ["pod_namespace", "pod_name", "disk_space"]
        pod_distribution_rows = [
            [
                find_in_dict_or_default(pod_uid_to_namespace, p["pod_uid"], ""),
                find_in_dict_or_default(pod_uid_to_name, p["pod_uid"], p["pod_uid"]),
                sum([c["disk_size"] for c in p["containers"]]),
            ]
            for p in pods_distribution
        ]
        pod_distribution_rows.sort(key=lambda row: row[2], reverse=True)
        for row in pod_distribution_rows:
            row[2] = humanize.naturalsize(row[2], binary=True)
        blocks.append(TableBlock(headers=pod_distribution_headers, rows=pod_distribution_rows))

    # calculate container-level disk distribution block
    if params.show_containers:
        container_distribution_headers = [
            "pod_namespace",
            "pod_name",
            "container_name",
            "disk_space",
        ]
        container_distribution_rows = []
        for p in pods_distribution:
            container_distribution_rows.extend(
                [
                    [
                        find_in_dict_or_default(pod_uid_to_namespace, p["pod_uid"], ""),
                        find_in_dict_or_default(pod_uid_to_name, p["pod_uid"], p["pod_uid"]),
                        find_in_dict_or_default(container_id_to_name, c["container_id"], c["container_id"]),
                        c["disk_size"],
                    ]
                    for c in p["containers"]
                ]
            )
        container_distribution_rows.sort(key=lambda row: (row[0], row[1], -row[3]))
        for row in container_distribution_rows:
            row[3] = humanize.naturalsize(row[3], binary=True)
        blocks.append(TableBlock(headers=container_distribution_headers, rows=container_distribution_rows))

    # calculate disk-tools warnings block
    if len(disk_info["pods_disk_info"]["warnings"]) > 0:
        warnings = "Encountered the following warnings while trying to get disk information of some containers:\n"
        for warning in disk_info["pods_disk_info"]["warnings"]:
            warnings += warning + "\n"
        blocks.append(MarkdownBlock(warnings))

    # Add enrichment
    event.add_enrichment(blocks)


def find_in_dict_or_default(d, item, default):
    if item in d:
        return d[item]
    return default
