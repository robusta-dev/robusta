import textwrap

import pygal
from pygal.style import DarkStyle as ChosenStyle
from robusta.api import *


class NodeCPUAnalysisParams(BaseModel):
    prometheus_url: str = None
    node: str = ""


def do_node_cpu_analysis(node: Node, prometheus_url: str = None) -> List[BaseBlock]:
    analyzer = NodeAnalyzer(node, prometheus_url)

    threshold = 0.005
    total_cpu_usage = analyzer.get_total_cpu_usage()
    total_container_cpu_usage = analyzer.get_total_containerized_cpu_usage()
    non_container_cpu_usage = total_cpu_usage - total_container_cpu_usage
    per_pod_usage_normalized = analyzer.get_per_pod_cpu_usage()
    per_pod_usage_unbounded = analyzer.get_per_pod_cpu_usage(
        threshold=threshold, normalize_by_cpu_count=False
    )
    per_pod_request = analyzer.get_per_pod_cpu_request()
    all_pod_names = list(
        set(per_pod_usage_unbounded.keys()).union(per_pod_request.keys())
    )

    treemap = pygal.Treemap(style=ChosenStyle)
    treemap.title = f"CPU Usage on Node {node.metadata.name}"
    treemap.value_formatter = lambda x: f"{int(x * 100)}%"
    treemap.add("Non-container usage", [non_container_cpu_usage])
    treemap.add("Free CPU", [1 - total_cpu_usage])
    for (pod_name, cpu_usage) in per_pod_usage_normalized.items():
        treemap.add(pod_name, [cpu_usage])

    MISSING_VALUE = -0.001
    bar_chart = pygal.Bar(x_label_rotation=-40, style=ChosenStyle)
    bar_chart.title = f"Actual Vs Requested vCPUs on Node {node.metadata.name}"
    bar_chart.x_labels = all_pod_names
    bar_chart.value_formatter = (
        lambda x: f"{x:.2f} vCPU" if x != MISSING_VALUE else "no data"
    )
    bar_chart.add(
        "Actual CPU Usage",
        [
            per_pod_usage_unbounded.get(pod_name, MISSING_VALUE)
            for pod_name in all_pod_names
        ],
    )
    bar_chart.add(
        "CPU Request",
        [per_pod_request.get(pod_name, MISSING_VALUE) for pod_name in all_pod_names],
    )

    return [
        HeaderBlock("Node CPU Analysis"),
        MarkdownBlock(
            f"_*Quick explanation:* High CPU typically occurs if you define pod CPU "
            f"requests incorrectly and Kubernetes schedules too many pods on one node. "
            f"If this is the case, update your pod CPU requests to more accurate numbers"
            f"using guidance from the attached graphs_"
        ),
        DividerBlock(),
        MarkdownBlock(
            textwrap.dedent(
                f"""\
                                        *Total CPU usage on node:* {int(total_cpu_usage * 100)}%
                                        *Container CPU usage on node:* {int(total_container_cpu_usage * 100)}%
                                        *Non-container CPU usage on node:* {int(non_container_cpu_usage * 100)}%
                                        """
            )
        ),
        DividerBlock(),
        MarkdownBlock(
            f"*Pods with CPU > {threshold * 100:0.1f}* (all numbers between 0-100% regardless of CPU count)"
        ),
        ListBlock(
            [
                f"{k}: *{v * 100:0.1f}%*"
                for (k, v) in per_pod_usage_normalized.items()
                if v >= threshold
            ]
        ),
        FileBlock("treemap.svg", treemap.render()),
        FileBlock("usage_vs_requested.svg", bar_chart.render()),
    ]


@on_manual_trigger
def node_cpu_analysis(event: ManualTriggerEvent):
    params = NodeCPUAnalysisParams(**event.data)
    node = Node().read(name=params.node)

    event.finding = Finding(
        title=f"Node CPU Usage Report for {params.node}",
        subject=FindingSubject(name=params.node),
        source=FindingSource.MANUAL,
        finding_type="node_cpu_analysis",
    )
    event.finding.add_enrichment(do_node_cpu_analysis(node, params.prometheus_url))
