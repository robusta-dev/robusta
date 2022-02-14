from robusta.api import *
from robusta.integrations.kubernetes.process_utils import ProcessFinder, ProcessType
from typing import List
import traceback

from robusta.integrations.kubernetes.custom_models import RobustaPod


@action
def java_process_inspector(event: PodEvent, params: ProcessParams):
    """
    Displays all java-toolkit debugging options for every java process
    """
    pod = event.get_pod()
    if not pod:
        logging.info(f"Java debugging - pod not found for event: {event}")
        return
    if not params.interactive:
        logging.info(f"unable to support non interactive jdk events")
        return

    finding = Finding(
        title=f"Java debugging session on pod {pod.metadata.name} in namespace {pod.metadata.namespace}:",
        source=FindingSource.MANUAL,
        aggregation_key="java_process_inspector",
        subject=FindingSubject(
            pod.metadata.name,
            FindingSubjectType.TYPE_POD,
            pod.metadata.namespace,
        ),
    )
    process_finder = ProcessFinder(pod, params, ProcessType.JAVA)
    if not process_finder.matching_processes:
        ERROR_MESSAGE = f"No relevant processes found for java debugging."
        logging.info(ERROR_MESSAGE)
        finding.add_enrichment(
            [MarkdownBlock(ERROR_MESSAGE)]
        )
        return
    finding.add_enrichment(
        [
            TableBlock(
                [[proc.pid, proc.exe, " ".join(proc.cmdline)] for proc in process_finder.matching_processes],
                ["pid", "exe", "cmdline"],
            )
        ]
    )
    finding = add_jdk_choices_to_finding(finding, params, process_finder.get_pids(), pod)
    event.add_finding(finding)


@action
def pod_jmap_pid(event: PodEvent, params: ProcessParams):
    """
        Runs jmap on a specific pid in your pod
    """
    jmap_cmd = "jmap"
    aggregation_key="pod_jmap_pid"
    run_jdk_command_on_pid(event, params, jmap_cmd, aggregation_key)


@action
def pod_jstack_pid(event: PodEvent, params: ProcessParams):
    """
        Runs jstack on a specific pid in your pod
    """
    jstack_cmd = "jstack"
    aggregation_key="pod_jstack_pid"
    run_jdk_command_on_pid(event, params, jstack_cmd, aggregation_key)


def run_jdk_command_on_pid(event: PodEvent, params: ProcessParams, cmd: str, aggregation_key: str):
    """
        A generic entrypoint function to run any jdk command via the java toolkit and creates a finding on it
    """
    if not params.pid:
        logging.info(f"{aggregation_key} - pid not found for event: {event}")
        return

    pod = event.get_pod()
    if not pod:
        logging.info(f"{aggregation_key} - pod not found for event: {event}")
        return

    finding = Finding(
        title=f"{cmd} run on pid {params.pid} in pod {pod.metadata.name} in namespace {pod.metadata.namespace}:",
        source=FindingSource.MANUAL,
        aggregation_key=aggregation_key,
        subject=FindingSubject(
            pod.metadata.name,
            FindingSubjectType.TYPE_POD,
            pod.metadata.namespace,
        ),
    )
    jdk_cmd = f"{cmd} {params.pid}"
    try:
        jdk_output = run_java_toolkit_command(jdk_cmd, pod)
        finding.add_enrichment(
            [
                [MarkdownBlock(f"{aggregation_key} ran on process [{params.pid}")],
                FileBlock(f"{aggregation_key}_{params.pid}.txt", jdk_output.encode()),
            ]
        )
    except Exception:
        finding.add_enrichment(
            [
                MarkdownBlock(f"```{traceback.format_exc()}```")
            ]
        )
    finally:
        event.add_finding(finding)


def run_java_toolkit_command(jdk_cmd: str, pod: RobustaPod ):
    java_toolkit_cmd = f"java-toolkit {jdk_cmd}"
    output = RobustaPod.exec_in_java_pod(
            pod.metadata.name,
            pod.spec.nodeName,
            java_toolkit_cmd )
    return output


def add_jdk_choices_to_finding(finding: Finding, params: ProcessParams, pids: List[int], pod: RobustaPod):
    finding.add_enrichment(
        [MarkdownBlock(f"Please select a JDK debugging choice:")]
    )
    choices = {}
    for pid in pids:
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
    return finding