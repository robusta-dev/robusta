import logging

from robusta.api import *


@on_report_callback
def daemonset_fix_config(event: ReportCallbackEvent):
    event.processing_context.create_finding(
        title="Proposed fix", source=SOURCE_CALLBACK, type=TYPE_PROMETHEUS_CALLBACK
    )
    event.processing_context.finding.add_enrichment(
        [
            MarkdownBlock(
                textwrap.dedent(
                    """\
        Add the following to your daemonset pod-template:
        ```
        tolerations:
        - effect: NoSchedule
          key: ToBeDeletedByClusterAutoscaler
          operator: Exists
        ```"""
                )
            )
        ]
    )

    event.processing_context.finding.add_enrichment(
        [
            MarkdownBlock(
                "This will tell Kubernetes that it is OK if daemonsets keep running while a node shuts down. "
                "This is desirable for daemonsets like elasticsearch which should keep gathering logs while the "
                "node shuts down."
                ""
            )
        ]
    )


@on_report_callback
def daemonset_silence_false_alarm(event: ReportCallbackEvent):
    event.processing_context.create_finding(
        title="Silence the alert", source=SOURCE_CALLBACK, type=TYPE_PROMETHEUS_CALLBACK
    )
    event.processing_context.finding.add_enrichment(
        [
            MarkdownBlock(
                textwrap.dedent(
                    """\
        Add the following to your `active_playbooks.yaml`:
        ```
          - name: "alerts_integration"
            action_params:
              alerts_config:
                (...)
                - alert_name: "KubernetesDaemonsetMisscheduled"
                  (...)
                  silencers:
                    - name: "DaemonsetMisscheduledSmartSilencer"
        ```"""
                )
            )
        ]
    )

    event.processing_context.finding.add_enrichment(
        [
            MarkdownBlock(
                "This will silence the KubernetesDaemonsetMisscheduled alert when the known false alarm occurs but not under "
                "other conditions."
                ""
            )
        ]
    )


def do_daemonset_enricher(ds: DaemonSet) -> List[BaseBlock]:
    return [
        MarkdownBlock(f"*Daemonset Stats for {ds.metadata.name}*"),
        KubernetesFieldsBlock(
            ds,
            [
                "status.desiredNumberScheduled",
                "status.currentNumberScheduled",
                "status.numberAvailable",
                "status.numberMisscheduled",
            ],
        ),
        MarkdownBlock(
            "_Daemonset lifecycle: pods start out as desired, then get scheduled, and then become available. "
            "If Kubernetes then decides a pod shouldn't be running on a node after all, it becomes "
            "misscheduled._"
        ),
    ]


# checks if the issue issue described here: https://blog.florentdelannoy.com/blog/2020/kube-daemonset-misscheduled/
# we check for it in the simplest way possible to avoid re-implementing k8s' scheduling logic for taints ourselves
def check_for_known_mismatch_false_alarm(ds: DaemonSet) -> bool:
    # if the daemonset was configured with an appropriate toleration, this false alarm isn't possible
    if does_daemonset_have_toleration(ds, "ToBeDeletedByClusterAutoscaler"):
        logging.info(
            f"daemonset is configured properly, so we don't have the known mismatch false alarm"
        )
        return False

    nodes_by_name = {n.metadata.name: n for n in NodeList.listNode().obj.items}
    ds_pods = RobustaPod.find_pods_with_direct_owner(
        ds.metadata.namespace, ds.metadata.uid
    )

    # look for at least one node where the false alarm is present
    for pod in ds_pods:
        if pod.spec.nodeName not in nodes_by_name:
            # we probably have a node that was created between the time we fetched the nodes and the time we fetched
            # the pods
            logging.warning(f"we have a pod not running on a known node. pod={pod}")
            continue

        relevant_node: Node = nodes_by_name[pod.spec.nodeName]
        if does_node_have_taint(relevant_node, "ToBeDeletedByClusterAutoscaler"):
            logging.info(
                f"we found a cluster being deleted by the autoscaler - we have the known mismatch false alert"
            )
            return True

    return False


def do_daemonset_mismatch_analysis(ds: DaemonSet) -> List[BaseBlock]:
    if not check_for_known_mismatch_false_alarm(ds):
        return []

    return [
        MarkdownBlock(
            "*Alert Cause*\n This specific firing of the alert is a *known false alarm* which occurs when the "
            "cluster autoscaler removes nodes running daemonsets which didn't explicitly request to remain running "
            "during node-shutdown."
        ),
        MarkdownBlock(
            textwrap.dedent(
                f"""\
            (<https://blog.florentdelannoy.com/blog/2020/kube-daemonset-misscheduled/|Learn more>).
            
            *Remediation*
            Would you like to:
    
            1. Fix the daemonset configuration to avoid the false alarm
            2. Use Robusta to silence the false alarm while passing through real alerts.
    
            Choose an option below to learn more."""
            )
        ),
        CallbackBlock(
            choices={
                "Fix the Configuration": daemonset_fix_config,
                "Silence the false alarm": daemonset_silence_false_alarm,
            },
            context={},
        ),
    ]


class DaemonsetAnalysisParams(SlackParams):
    daemonset_name: str
    namespace: str


@on_manual_trigger
def daemonset_mismatch_analysis(event: ManualTriggerEvent):
    params = DaemonsetAnalysisParams(**event.data)
    ds = DaemonSet().read(name=params.daemonset_name, namespace=params.namespace)
    event.processing_context.create_finding(
        title="Daemonset Mismatch Analysis",
        source=SOURCE_MANUAL,
        type=TYPE_DEPLOYMENT_MISMATCH,
    )
    event.processing_context.finding.add_enrichment(
        [do_daemonset_enricher(ds)], annotations={"unfurl": "False"}
    )
    event.processing_context.finding.add_enrichment(
        [do_daemonset_mismatch_analysis(ds)]
    )
