from robusta.api import *
from robusta.utils.parsing import load_json

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

    # run disk-tools on node and parse its json output
    pods_distribution_str_info = RobustaPod.run_debugger_pod(
        node.metadata.name,
        pod_image="us-central1-docker.pkg.dev/genuine-flight-317411/devel/disk-tools:1.0",
        env=[
            EnvVar(
                name="CURRENT_POD_NAME",
                valueFrom=EnvVarSource(fieldRef=ObjectFieldSelector(fieldPath="metadata.name"))
            ),
            EnvVar(
                name="CURRENT_POD_NAMESPACE",
                valueFrom=EnvVarSource(fieldRef=ObjectFieldSelector(fieldPath="metadata.namespace"))
            )
        ],
        mount_host_root=True
    )

    # The code for the disk-tools image can be found in https://github.com/robusta-dev/disk-tools
    # Please refer to this code in order to see the structure of the json that is returned

    pods_distribution_info = load_json(pods_distribution_str_info)
    pods_distribution = pods_distribution_info["pods_disk_distribution"]["pods_distribution"]

    # calculate disk info
    disk_stats = pods_distribution_info["disk_stats"]
    used_bytes = disk_stats["used"]
    total_bytes = disk_stats["total"]
    total_pod_disk_space_in_bytes = 0
    for p in pods_distribution:
        for c in p["containers"]:
            total_pod_disk_space_in_bytes += c["disk_size"]

    used = humanize.naturalsize(used_bytes, binary=True)
    used_percentage = round(used_bytes/total_bytes*100, 2)
    total_pod_disk_space = humanize.naturalsize(total_pod_disk_space_in_bytes, binary=True)
    other_disk_space = humanize.naturalsize(used_bytes - total_pod_disk_space_in_bytes, binary=True)
    blocks.append(MarkdownBlock(f"Disk analysis for node {node.metadata.name} follows.\n"
                                f"The used disk space is currently at {used} ({used_percentage}%).\n"
                                f"Of this space, {total_pod_disk_space} is used by pods "
                                f"and the rest ({other_disk_space}) is consumed by the node."))

    # calculate pod-level disk distribution
    pod_distribution_headers = ["pod_namespace", "pod_name", "disk_space"]
    pod_distribution_rows = [
        [
            p["pod_namespace"],
            p["pod_name"],
            sum([c["disk_size"] for c in p["containers"]])
        ] for p in pods_distribution
    ]
    pod_distribution_rows.sort(key=lambda row: row[2], reverse=True)
    for row in pod_distribution_rows:
        row[2] = humanize.naturalsize(row[2], binary=True)
    blocks.append(TableBlock(headers=pod_distribution_headers, rows=pod_distribution_rows))

    # calculate container-level disk distribution
    container_distribution_headers = ["pod_namespace", "pod_name", "container_name", "disk_space"]
    container_distribution_rows = []
    for pod in pods_distribution:
        container_distribution_rows.extend(
            [
                [
                    pod["pod_namespace"],
                    pod["pod_name"],
                    container["container_name"],
                    container["disk_size"]
                ] for container in pod["containers"]
            ]
        )
    container_distribution_rows.sort(key=lambda row: (row[0], row[1], -row[3]))
    for row in container_distribution_rows:
        row[3] = humanize.naturalsize(row[3], binary=True)
    blocks.append(TableBlock(headers=container_distribution_headers, rows=container_distribution_rows))

    # calculate disk-tools warnings
    if len(pods_distribution_info["pods_disk_distribution"]["warnings"]) > 0:
        warnings = "Failed to get disk information of some containers:\n"
        for warning in pods_distribution_info["pods_disk_distribution"]["warnings"]:
            warnings += warning + "\n"
        blocks.append(MarkdownBlock(warnings))

    # Add enrichment
    event.add_enrichment(blocks)
