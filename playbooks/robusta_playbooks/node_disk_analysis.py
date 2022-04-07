from robusta.api import *
from robusta.utils.parsing import load_json

import re

import humanize


@action
def node_disk_analyzer(event: NodeEvent):
    """
    Provides relevant disk information for troubleshooting disk issues.
    Currently, the following information is provided:
        1. The total disk space used by pods, and the total disk space used by the node for other purposes
        2. Disk usage of pods, sorted from highest to lowest
        3. Disk usage of containers, sorted (separately for every pod) from highest to lowest
    """
    node = event.get_node()
    if not node:
        logging.error(
            f"cannot run node disk analysis on event with no node object: {event}"
        )
        return

    blocks: List[BaseBlock] = []

    # map pod names and namespaces by pod uid, and container names by container id
    node_pods: PodList = Pod.listPodForAllNamespaces(
            field_selector=f"spec.nodeName={node.metadata.name}"
        ).obj

    pod_uid_to_name: Dict[str, str] = {}
    pod_uid_to_namespace: Dict[str, str] = {}
    container_id_to_name: Dict[str, str] = {}

    for pod in node_pods.items:
        pod_uid_to_name[pod.metadata.uid] = pod.metadata.name
        pod_uid_to_namespace[pod.metadata.uid] = pod.metadata.namespace

        for container_status in pod.status.containerStatuses:
            container_id = re.match(".*//(.*)$", container_status.containerID).group(1)
            container_id_to_name[container_id] = container_status.name

    # run disk-tools on node and parse its json output
    disk_info_str = RobustaPod.run_debugger_pod(
        node.metadata.name,
        pod_image="us-central1-docker.pkg.dev/genuine-flight-317411/devel/disk-tools:1.3",
        env=[
            EnvVar(
                name="CURRENT_POD_UID",
                valueFrom=EnvVarSource(fieldRef=ObjectFieldSelector(fieldPath="metadata.uid"))
            )
        ],
        mount_host_root=True
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
    used_percentage = round(used_bytes/total_bytes*100, 2)
    total_pod_disk_space = humanize.naturalsize(total_pods_disk_space_in_bytes, binary=True)
    other_disk_space = humanize.naturalsize(used_bytes - total_pods_disk_space_in_bytes, binary=True)
    blocks.append(MarkdownBlock(f"Disk analysis for node {node.metadata.name} follows.\n"
                                f"The used disk space is currently at {used} out of {total} ({used_percentage}%).\n"
                                f"Of this space, {total_pod_disk_space} is used by pods "
                                f"and the rest ({other_disk_space}) is consumed by the node."))

    # calculate pod-level disk distribution block
    pod_distribution_headers = ["pod_namespace", "pod_name", "disk_space"]
    pod_distribution_rows = [
        [
            find_in_dict_or_default(pod_uid_to_namespace, p["pod_uid"], ""),
            find_in_dict_or_default(pod_uid_to_name, p["pod_uid"], p["pod_uid"]),
            sum([c["disk_size"] for c in p["containers"]])
        ] for p in pods_distribution
    ]
    pod_distribution_rows.sort(key=lambda row: row[2], reverse=True)
    for row in pod_distribution_rows:
        row[2] = humanize.naturalsize(row[2], binary=True)
    blocks.append(TableBlock(headers=pod_distribution_headers, rows=pod_distribution_rows))

    # calculate container-level disk distribution block
    container_distribution_headers = ["pod_namespace", "pod_name", "container_name", "disk_space"]
    container_distribution_rows = []
    for p in pods_distribution:
        container_distribution_rows.extend(
            [
                [
                    find_in_dict_or_default(pod_uid_to_namespace, p["pod_uid"], ""),
                    find_in_dict_or_default(pod_uid_to_name, p["pod_uid"], p["pod_uid"]),
                    find_in_dict_or_default(container_id_to_name, c["container_id"], c["container_id"]),
                    c["disk_size"]
                ] for c in p["containers"]
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
