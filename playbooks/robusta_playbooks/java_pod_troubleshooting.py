from robusta.api import *
from robusta.integrations.kubernetes.process_utils import ProcessFinder, ProcessType
from robusta.utils.parsing import load_json
from typing import List

#from robusta.integrations.kubernetes.custom_models import JAVA_DEBUGGER_IMAGE

JAVA_DEBUGGER_IMAGE = (
    "gcr.io/genuine-flight-317411/java-toolkit/jtk-11:latest"
)

@action
def java_debugger(event: PodEvent, params: ProcessParams):
    """

    """
    pod = event.get_pod()
    if not pod:
        logging.info(f"Java debugging - pod not found for event: {event}")
        return
    finding = Finding(
        title=f"Java debugging session on pod {pod.metadata.name} in namespace {pod.metadata.namespace}:",
        source=FindingSource.MANUAL,
        aggregation_key="java_debugger",
        subject=FindingSubject(
            pod.metadata.name,
            FindingSubjectType.TYPE_POD,
            pod.metadata.namespace,
        ),
    )
    process_finder = ProcessFinder(pod, params, ProcessType.JAVA)
    java_pids = process_finder.get_pids()
    if not java_pids:
        ERROR_MESSAGE = f"No relevant processes found for advanced debugging."
        logging.info(ERROR_MESSAGE)
        finding.add_enrichment(
            [MarkdownBlock(ERROR_MESSAGE)]
        )
        return
    logging.info("jdk_choices_in_finding_for_pid")
    finding.add_enrichment(
        [MarkdownBlock(f"Please select an advanced debugging choice:")]
    )
    choices = {}
    for pid in java_pids:
        logging.info(f"jdk_choices_in_finding_for_pid {pid}")
        updated_params = params.copy()
        updated_params.process_substring = ""
        updated_params.pid = pid
        choices[f"jmap {updated_params.pid}"] = CallbackChoice(
            action=pod_jmap_pid,
            action_params=updated_params,
            kubernetes_object=pod,
        )
        choices[f"jstack {updated_params.pid}"] = CallbackChoice(
            action=pod_jstack_pid,
            action_params=updated_params,
            kubernetes_object=pod,
        )
    finding.add_enrichment([CallbackBlock(choices),
                            MarkdownBlock(
                                "*After clicking a button please wait up to 120 seconds for a response*"
                            )
                            ])
    event.add_finding(finding)
    #jdk_choices_in_finding_for_pid(finding, params, java_pid, pod)


@action
def pod_jmap_pid(event: PodEvent, params: ProcessParams):
    """

    """
    pod = event.get_pod()
    if not pod:
        logging.info(f"pod_jmap_pid - pod not found for event: {event}")
        return

    if not params.pid:
        logging.info(f"pod_jmap_pid - pid not found for event: {event}")
        return
    jmap_cmd = f"jmap {params.pid}"
    finding, jmap_output = run_jdk_command(jmap_cmd, pod.metadata, "pod_jmap_pid")
    finding.add_enrichment(
        [
            [MarkdownBlock(f"jmap ran on process [{params.pid}")],
            FileBlock(f"jmap_{params.pid}.txt", jmap_output.encode()),
        ]
    )
    event.add_finding(finding)


@action
def pod_jstack_pid(event: PodEvent, params: ProcessParams):
    """

    """
    pod = event.get_pod()
    if not pod:
        logging.info(f"pod_jstack_pid - pod not found for event: {event}")
        return

    if not params.pid:
        logging.info(f"pod_jstack_pid - pid not found for event: {event}")
        return
    jmap_cmd = f"jstack {params.pid}"
    finding, jmap_output = run_jdk_command(jmap_cmd, pod.metadata, "pod_jstack_pid")
    finding.add_enrichment(
        [
            [MarkdownBlock(f"jstack_pid ran on process [{params.pid}")],
            FileBlock(f"jstack_{params.pid}.txt", jmap_output.encode()),
        ]
    )
    event.add_finding(finding)

def run_jdk_command(jdk_cmd: str, pod_meta: ObjectMeta, aggregation_key ):
    finding = Finding(
        title=f"Running Java-toolkit in pod {pod_meta.name} in namespace {pod_meta.namespace}:",
        source=FindingSource.MANUAL,
        aggregation_key=aggregation_key,
        subject=FindingSubject(
            pod_meta.name,
            FindingSubjectType.TYPE_POD,
            pod_meta.namespace,
        ),
    )
    cmd = f"k=java-toolkit {jdk_cmd}"
    output = RobustaPod.exec_in_debugger_pod(
            pod_meta.name,
            pod_meta.namespace,
            cmd, debug_image=JAVA_DEBUGGER_IMAGE, command_timeout=90
        )
    return finding, output


def jdk_choices_in_finding_for_pid(finding: Finding, params: ProcessParams, pid: int, pod: RobustaPod):
    finding.add_enrichment(
        [MarkdownBlock(f"Please select an advanced debugging choice:")]
    )
    if params.interactive:
        choices = {}
        updated_params = params.copy()
        updated_params.process_substring = ""
        updated_params.pid = pid
        choices[f"jmap {updated_params.pid}"] = CallbackChoice(
            action=pod_jmap_pid,
            action_params=updated_params,
            kubernetes_object=pod,
        )
        choices[f"jstack {updated_params.pid}"] = CallbackChoice(
            action=pod_jstack_pid,
            action_params=updated_params,
            kubernetes_object=pod,
        )
        finding.add_enrichment([CallbackBlock(choices),
                                MarkdownBlock(
                                    "*After clicking a button please wait up to 120 seconds for a response*"
                                )
                                ])
    return finding