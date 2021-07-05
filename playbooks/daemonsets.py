from robusta.api import *


@on_report_callback
def daemonset_fix_config(event: ReportCallbackEvent):
    event.report_blocks.append(MarkdownBlock(textwrap.dedent("""\
        Add the following to your daemonset pod-template:
        ```
        tolerations:
        - effect: NoSchedule
          key: ToBeDeletedByClusterAutoscaler
          operator: Exists
        ```""")))

    event.report_blocks.append(MarkdownBlock(
        "This will tell Kubernetes that it is OK if daemonsets keep running while a node shuts down. "
        "This is desirable for daemonsets like elasticsearch which should keep gathering logs while the "
        "node shuts down."""))

    send_to_slack(event)


@on_report_callback
def daemonset_silence_false_alarm(event: ReportCallbackEvent):
    event.report_blocks.append(MarkdownBlock(textwrap.dedent("""\
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
        ```""")))

    event.report_blocks.append((MarkdownBlock(
        "This will silence the KubernetesDaemonsetMisscheduled alert when the known false alarm occurs but not under "
        "other conditions.""")))

    send_to_slack(event)


def do_daemonset_enricher(ds: DaemonSet) -> List[BaseBlock]:
    return [
        MarkdownBlock(f"*Daemonset Stats for {ds.metadata.name}*"),
        KubernetesFieldsBlock(ds,
                              ["status.desiredNumberScheduled",
                               "status.currentNumberScheduled",
                               "status.numberAvailable",
                               "status.numberMisscheduled"],
                              ),
        MarkdownBlock("_Daemonset lifecycle: pods start out as desired, then get scheduled, and then become available. "
                      "If Kubernetes then decides a pod shouldn't be running on a node after all, it becomes "
                      "misscheduled._")
    ]


# checks if the issue issue described here: https://blog.florentdelannoy.com/blog/2020/kube-daemonset-misscheduled/
# we check for it in the simplest way possible to avoid re-implementing k8s' scheduling logic for taints ourselves
def check_for_known_mismatch_false_alarm(ds: DaemonSet) -> bool:
    nodes_by_name = {n.metadata.name: n for n in NodeList.listNode().obj.items}
    ds_pods = RobustaPod.find_pods_with_owner(ds.metadata.namespace, ds.metadata.uid)

    # if the daemonset was configured with an appropriate toleration, this false alarm isn't possible
    if does_daemonset_have_toleration(ds, "ToBeDeletedByClusterAutoscaler"):
        return False

    # look for at least one node where the false alarm is present
    for pod in ds_pods:
        relevant_node: Node = nodes_by_name[pod.spec.nodeName]
        if does_node_have_taint(relevant_node, "ToBeDeletedByClusterAutoscaler"):
            return True

    return False


def do_daemonset_mismatch_analysis(ds: DaemonSet) -> List[BaseBlock]:
    # TODO: there is a race condition here between getting the list of daemonsets and the list of nodes
    if not check_for_known_mismatch_false_alarm(ds):
        return []

    return [
        MarkdownBlock(
            "*Alert Cause*\n This specific firing of the alert is a *known false alarm* which occurs when the "
            "cluster autoscaler removes nodes running daemonsets which didn't explicitly request to remain running "
            "during node-shutdown."),

        MarkdownBlock(textwrap.dedent(f"""\
            (<https://blog.florentdelannoy.com/blog/2020/kube-daemonset-misscheduled/|Learn more>).
            
            *Remediation*
            Would you like to:
    
            1. Fix the daemonset configuration to avoid the false alarm
            2. Use Robusta to silence the false alarm while passing through real alerts.
    
            Choose an option below to learn more.""")),
        CallbackBlock(choices={"Fix the Configuration": daemonset_fix_config,
                               "Silence the false alarm": daemonset_silence_false_alarm},
                      context={})]


class DaemonsetAnalysisParams(BaseModel):
    daemonset_name: str
    namespace: str
    slack_channel: str


@on_manual_trigger
def daemonset_mismatch_analysis(event: ManualTriggerEvent):
    params = DaemonsetAnalysisParams(**event.data)
    ds = DaemonSet().read(name=params.daemonset_name, namespace=params.namespace)
    event.report_blocks.extend(do_daemonset_enricher(ds))
    event.report_blocks.extend(do_daemonset_mismatch_analysis(ds))
    event.slack_channel = params.slack_channel
    event.slack_allow_unfurl = False
    send_to_slack(event)
