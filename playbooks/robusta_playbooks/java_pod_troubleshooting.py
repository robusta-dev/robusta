import logging
import traceback
from typing import Callable, Dict, List, Optional

from robusta.api import (
    CallbackBlock,
    CallbackChoice,
    FileBlock,
    Finding,
    FindingSource,
    FindingType,
    MarkdownBlock,
    PodEvent,
    PodFindingSubject,
    ProcessFinder,
    ProcessParams,
    ProcessType,
    RobustaPod,
    TableBlock,
    action,
)


class JavaParams(ProcessParams):
    """
    :var jtk_image: the java-toolkit image to use for debugging
    """

    jtk_image: str = None  # type: ignore


@action
def java_process_inspector(event: PodEvent, params: JavaParams):
    """
    Displays all java-toolkit debugging options for every java process
    """
    pod = event.get_pod()
    if not pod:
        logging.info(f"Java debugging - pod not found for event: {event}")
        return
    if not params.interactive:
        logging.info("unable to support non interactive jdk events")
        return

    finding = Finding(
        title=f"Java debugging session on pod {pod.metadata.name} in namespace {pod.metadata.namespace}:",
        source=FindingSource.MANUAL,
        aggregation_key="JavaProcessInspector",
        subject=PodFindingSubject(pod),
        finding_type=FindingType.REPORT,
        failure=False,
    )
    process_finder = ProcessFinder(pod, params, ProcessType.JAVA)
    if not process_finder.matching_processes:
        ERROR_MESSAGE = "No relevant processes found for java debugging."
        logging.info(ERROR_MESSAGE)
        finding.add_enrichment([MarkdownBlock(ERROR_MESSAGE)])
        event.add_finding(finding)
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
def pod_jmap_pid(event: PodEvent, params: JavaParams):
    """
    Runs jmap on a specific pid in your pod
    """
    jmap_cmd = "jmap"
    aggregation_key = "PodJmapPid"
    run_jdk_command_on_pid(event, params, jmap_cmd, aggregation_key, pod_jmap_pid)


@action
def pod_jstack_pid(event: PodEvent, params: JavaParams):
    """
    Runs jstack on a specific pid in your pod
    """
    jstack_cmd = "jstack"
    aggregation_key = "PodJstackPid"
    run_jdk_command_on_pid(event, params, jstack_cmd, aggregation_key, pod_jstack_pid)


def run_jdk_command_on_pid(
    event: PodEvent,
    params: JavaParams,
    cmd: str,
    aggregation_key: str,
    retrigger_action: Callable,
):
    """
    A generic entrypoint function to run any jdk command via the java toolkit and creates a finding on it
    """
    pod = event.get_pod()
    if not pod:
        logging.info(f"{aggregation_key} - pod not found for event: {event}")
        return

    finding = Finding(
        title=f"{cmd} run on pid {params.pid} in pod {pod.metadata.name} in namespace {pod.metadata.namespace}:",
        source=FindingSource.MANUAL,
        aggregation_key=aggregation_key,
        subject=PodFindingSubject(pod),
        finding_type=FindingType.REPORT,
        failure=False,
    )

    if not params.pid:
        process_finder = ProcessFinder(pod, params, ProcessType.JAVA)
        process = process_finder.get_match_or_report_error(finding, cmd, retrigger_action, java_process_inspector)
        if process is None:
            event.add_finding(finding)
            return
        params.pid = process.pid

    jdk_cmd = f"{cmd} {params.pid}"
    try:
        jdk_output = run_java_toolkit_command(jdk_cmd, pod, params.jtk_image, custom_annotations=params.custom_annotations)
        finding.add_enrichment(
            [
                MarkdownBlock(f"{aggregation_key} ran on process {params.pid}"),
                FileBlock(f"{aggregation_key}_{params.pid}.txt", jdk_output.encode()),
            ]
        )
    except Exception:
        finding.add_enrichment([MarkdownBlock(f"```{traceback.format_exc()}```")])
    finally:
        event.add_finding(finding)


def run_java_toolkit_command(
    jdk_cmd: str, pod: RobustaPod, override_jtk_image: str, custom_annotations: Optional[Dict[str, str]]
):
    java_toolkit_cmd = f"java-toolkit {jdk_cmd}"
    if override_jtk_image:
        return RobustaPod.exec_in_java_pod(
            pod.metadata.name,
            pod.spec.nodeName,
            java_toolkit_cmd,
            override_jtk_image=override_jtk_image,
            custom_annotations=custom_annotations,
        )
    return RobustaPod.exec_in_java_pod(
        pod.metadata.name, pod.spec.nodeName, java_toolkit_cmd, custom_annotations=custom_annotations
    )


def add_jdk_choices_to_finding(finding: Finding, params: JavaParams, pids: List[int], pod: RobustaPod) -> Finding:
    finding.add_enrichment([MarkdownBlock("Please select a Java troubleshooting choice:")])
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
    finding.add_enrichment(
        [
            CallbackBlock(choices),
            MarkdownBlock("*After clicking a button please wait up to 120 seconds for a response*"),
        ]
    )
    return finding
