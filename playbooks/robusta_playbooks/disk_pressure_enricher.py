from robusta.api import *
from robusta.integrations.resource_analysis.disk_analyzer import DiskTransformer


@action
def disk_pressure_enricher(event: NodeEvent):
    """
    Provides relevant disk information for troubleshooting disk pressure issues when the disk on a node is filling up.
    """
    node = event.get_node()
    if not node:
        logging.error(
            f"cannot run disk pressure enricher on event with no node object: {event}"
        )
        return

    blocks: List[BaseBlock] = []

    # run disk-tools on node and parse its json output
    pods_distribution_str_info = RobustaPod.run_privileged_pod(
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
    pods_distribution_info = json.loads(pods_distribution_str_info)
    pods_distribution = pods_distribution_info["pods_disk_distribution"]["pods_distribution"]

    # report disk-tools warnings
    for warning in pods_distribution_info["pods_disk_distribution"]["warnings"]:
        logging.warning(warning)

    # calculate disk info
    disk_stats = pods_distribution_info["disk_stats"]
    used_bytes = disk_stats["used"]
    total_bytes = disk_stats["total"]
    total_pod_disk_space_in_bytes = 0
    for p in pods_distribution:
        for c in p["containers"]:
            total_pod_disk_space_in_bytes += c["disk_size"]

    used = DiskTransformer.get_readable_form(used_bytes)
    used_percentage = round(used_bytes/total_bytes*100, 2)
    total_pod_disk_space = DiskTransformer.get_readable_form(total_pod_disk_space_in_bytes)
    other_disk_space = DiskTransformer.get_readable_form(used_bytes - total_pod_disk_space_in_bytes)
    blocks.append(MarkdownBlock(f"Disk is filling up on node {node.metadata.name}.\n"
                                f"The used disk space is currently at {used} ({used_percentage}%).\n"
                                f"Of this space, {total_pod_disk_space} is used by pods "
                                f"and the rest ({other_disk_space}) is consumed by the node"))

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
        row[2] = DiskTransformer.get_readable_form(row[2])
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
        row[3] = DiskTransformer.get_readable_form(row[3])
    blocks.append(TableBlock(headers=container_distribution_headers, rows=container_distribution_rows))

    # Add enrichment
    event.add_enrichment(blocks)
