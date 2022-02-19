from robusta.api import *


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

    # Run disk-tools on node and parse its json output
    pods_distribution_str_info = RobustaPod.exec_in_debugger_pod(
        node.metadata.name,
        node.metadata.name,
        "python3 /app/src/pods_distribution.py",
        debug_image="us-central1-docker.pkg.dev/genuine-flight-317411/devel/disk-tools:1.0"
    )
    pods_distribution_info = json.loads(pods_distribution_str_info)

    # report disk-tools warnings
    for warning in pods_distribution_info["pods_disk_distribution"]["warnings"]:
        logging.warning(warning)

    # calculate pod-level disk distribution
    pod_distribution_headers = ["pod_namespace", "pod_name", "disk_space"]
    pod_distribution_rows = [
        [
            pod["pod_namespace"],
            pod["pod_name"],
            sum([container["disk_size"] for container in pod["containers"]])
        ] for pod in pods_distribution_info["pods_disk_distribution"]["pods_distribution"]
    ]
    pod_distribution_rows.sort(key= lambda row: row[2], reverse = True)
    event.add_enrichment([TableBlock(headers=pod_distribution_headers, rows=pod_distribution_rows)])

    # calculate container-level disk distribution
    container_distribution_headers = ["pod_namespace", "pod_name", "disk_space"]
    container_distribution_rows = []
    for pod in pods_distribution_info["pods_disk_distribution"]["pods_distribution"]:
        container_distribution_rows.extend(
            [
                [
                    pod["pod_namespace"],
                    pod["pod_name"],
                    container["disk_size"]
                ] for container in pod["containers"]
            ]
        )
    pod_distribution_rows.sort(key=lambda row: (row[0], row[1], -row[2]))
    event.add_enrichment([TableBlock(headers=container_distribution_headers, rows=container_distribution_rows)])
