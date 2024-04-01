import logging
import textwrap

from hikaru.model.rel_1_26 import DaemonSet, Node, NodeList
from robusta.api import (
    CallbackBlock,
    CallbackChoice,
    DaemonSetEvent,
    ExecutionBaseEvent,
    Finding,
    FindingSource,
    KubernetesFieldsBlock,
    MarkdownBlock,
    PrometheusKubernetesAlert,
    RobustaPod,
    action,
    does_daemonset_have_toleration,
    does_node_have_taint,
)


@action
def daemonset_fix_config(event: ExecutionBaseEvent):
    finding = Finding(
        title="Proposed fix",
        source=FindingSource.CALLBACK.value,
        aggregation_key="DaemonsetFixConfig",
    )
    finding.add_enrichment(
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

    finding.add_enrichment(
        [
            MarkdownBlock(
                "This will tell Kubernetes that it is OK if daemonsets keep running while a node shuts down. "
                "This is desirable for daemonsets like elasticsearch which should keep gathering logs while the "
                "node shuts down."
                ""
            )
        ]
    )
    event.add_finding(finding)


@action
def daemonset_silence_false_alarm(event: ExecutionBaseEvent):
    finding = Finding(
        title="Silence the alert",
        source=FindingSource.CALLBACK,
        aggregation_key="DaemonsetSilenceFalseAlarm",
    )
    finding.add_enrichment(
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

    finding.add_enrichment(
        [
            MarkdownBlock(
                "This will silence the KubernetesDaemonsetMisscheduled alert when the known false alarm occurs but not under "
                "other conditions."
                ""
            )
        ]
    )
    event.add_finding(finding)


@action
def daemonset_status_enricher(event: DaemonSetEvent):
    """
    Enrich the finding with daemon set stats.

    Includes recommendations for the identified cause.
    """
    ds = event.get_daemonset()
    if not ds:
        logging.error(f"cannot run DaemonsetEnricher on event with no daemonset: {event}")
        return

    event.add_enrichment(
        [
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
    )


# checks if the issue described here: https://blog.florentdelannoy.com/blog/2020/kube-daemonset-misscheduled/
# we check for it in the simplest way possible to avoid re-implementing k8s' scheduling logic for taints ourselves
def check_for_known_mismatch_false_alarm(ds: DaemonSet) -> bool:
    # if the daemonset was configured with an appropriate toleration, this false alarm isn't possible
    if does_daemonset_have_toleration(ds, "ToBeDeletedByClusterAutoscaler"):
        logging.info("daemonset is configured properly, so we don't have the known mismatch false alarm")
        return False

    nodes_by_name = {n.metadata.name: n for n in NodeList.listNode().obj.items}
    ds_pods = RobustaPod.find_pods_with_direct_owner(ds.metadata.namespace, ds.metadata.uid)

    # look for at least one node where the false alarm is present
    for pod in ds_pods:
        if pod.spec.nodeName not in nodes_by_name:
            # we probably have a node that was created between the time we fetched the nodes and the time we fetched
            # the pods
            logging.warning(f"we have a pod not running on a known node. pod={pod}")
            continue

        relevant_node: Node = nodes_by_name[pod.spec.nodeName]
        if does_node_have_taint(relevant_node, "ToBeDeletedByClusterAutoscaler"):
            logging.info("we found a cluster being deleted by the autoscaler - we have the known mismatch false alert")
            return True

    return False


@action
def daemonset_misscheduled_smart_silencer(alert: PrometheusKubernetesAlert):
    """
    Silence daemonset misscheduled alert finding if it's a known false alarm.
    """
    if not alert.daemonset:
        return
    alert.stop_processing = check_for_known_mismatch_false_alarm(alert.daemonset)


@action
def daemonset_misscheduled_analysis_enricher(event: DaemonSetEvent):
    """
    Enrich the alert finding with analysis and possible causes for the misscheduling, if the cause is identified.
    """
    ds = event.get_daemonset()
    if not ds:
        logging.error(f"cannot run DaemonsetMisscheduledAnalysis on event with no daemonset: {event}")
        return

    if not check_for_known_mismatch_false_alarm(ds):
        return

    event.add_enrichment(
        [
            MarkdownBlock(
                "*Alert Cause*\n This specific firing of the alert is a *known false alarm* which occurs when the "
                "cluster autoscaler removes nodes running daemonsets which didn't explicitly request to remain running "
                "during node-shutdown."
            ),
            MarkdownBlock(
                textwrap.dedent(
                    """\
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
                    "Fix the Configuration": CallbackChoice(action=daemonset_fix_config),
                    "Silence the false alarm": CallbackChoice(action=daemonset_silence_false_alarm),
                },
            ),
        ]
    )
