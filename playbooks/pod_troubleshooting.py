# playbooks for peeking inside running pods
import textwrap
import humanize
from robusta.api import *
from typing import List


class StartProfilingParams(BaseModel):
    seconds: int = 2
    process_name: str = ""
    include_idle: bool = False


@action
def python_profiler(event: PodEvent, action_params: StartProfilingParams):
    # This should use ephemeral containers, but they aren't in GA yet. To enable them on GCP for example,
    # you need to create a brand new cluster. Therefore we're sticking with regular containers for now
    pod = event.get_pod()
    if not pod:
        logging.info(f"python_profiler - pod not found for event: {event}")
        return
    processes = pod.get_processes()
    debugger = RobustaPod.create_debugger_pod(pod.metadata.name, pod.spec.nodeName)

    try:
        finding = Finding(
            title=f"Profile results for {pod.metadata.name} in namespace {pod.metadata.namespace}:",
            source=FindingSource.MANUAL,
            aggregation_key="python_profiler",
            subject=FindingSubject(
                pod.metadata.name,
                FindingSubjectType.TYPE_POD,
                pod.metadata.namespace,
            ),
        )

        for target_proc in processes:
            target_cmd = " ".join(target_proc.cmdline)
            if action_params.process_name not in target_cmd:
                logging.info(
                    f"skipping process because it doesn't match process_name. {target_cmd}"
                )
                continue
            elif "python" not in target_proc.exe:
                logging.info(
                    f"skipping process because it doesn't look like a python process. {target_cmd}"
                )
                continue

            filename = "/profile.svg"
            pyspy_cmd = f"py-spy record --duration={action_params.seconds} --pid={target_proc.pid} --rate 30 --nonblocking -o {filename} {'--idle' if action_params.include_idle else ''}"
            logging.info(
                f"starting to run profiler on {target_cmd} with pyspy command: {pyspy_cmd}"
            )
            pyspy_output = debugger.exec(pyspy_cmd)
            if "Error:" in pyspy_output:
                logging.info(f"error profiler on {target_cmd}. error={pyspy_output}")
                continue

            logging.info(f"done running profiler on {target_cmd}")
            svg = debugger.exec(f"cat {filename}")
            finding.add_enrichment([FileBlock(f"{target_cmd}.svg", svg)])
        event.add_finding(finding)

    finally:
        debugger.deleteNamespacedPod(
            debugger.metadata.name, debugger.metadata.namespace
        )


@action
def pod_ps(event: PodEvent):
    pod = event.get_pod()
    if not pod:
        logging.info(f"pod_ps - pod not found for event: {event}")
        return

    logging.info(f"getting info for: {pod.metadata.name}")

    processes = pod.get_processes()
    finding = Finding(
        title=f"Processes in pod {pod.metadata.name} in namespace {pod.metadata.namespace}:",
        source=FindingSource.MANUAL,
        aggregation_key="pod_processes",
        subject=FindingSubject(
            pod.metadata.name,
            FindingSubjectType.TYPE_POD,
            pod.metadata.namespace,
        ),
    )
    finding.add_enrichment(
        [
            TableBlock(
                [[proc.pid, proc.exe, " ".join(proc.cmdline)] for proc in processes],
                ["pid", "exe", "cmdline"],
            )
        ]
    )
    event.add_finding(finding)


class MemoryTraceParams(BaseModel):
    process_substring: str
    seconds: int = 60


class PythonMemoryStatistic(BaseModel):
    size: int
    count: int
    traceback: List[str] = []

    def to_markdown(self):
        formatted_tb = "\n".join(self.traceback)
        if formatted_tb:
            formatted_tb = f"```\n{formatted_tb}\n```"
        return textwrap.dedent(
            f"*{humanize.naturalsize(self.size)} from {self.count} allocations*\n{formatted_tb}"
        )


class PythonMemorySnapshot(BaseModel):
    data: List[PythonMemoryStatistic]
    other_data: PythonMemoryStatistic
    total: int
    overhead: int


@action
def python_memory(event: PodEvent, params: MemoryTraceParams):
    pod = event.get_pod()
    if not pod:
        logging.info(f"python_memory - pod not found for event: {event}")
        return

    find_pid_cmd = f"debug-toolkit find-pid '{pod.metadata.uid}' '{params.process_substring}' python"
    cmd = f"debug-toolkit memory --seconds={params.seconds} `{find_pid_cmd}`"
    output = RobustaPod.exec_in_debugger_pod(pod.metadata.name, pod.spec.nodeName, cmd)
    snapshot = PythonMemorySnapshot(**json.loads(output))

    finding = Finding(
        title=f"Memory allocations for {pod.metadata.name} in namespace {pod.metadata.namespace}:",
        source=FindingSource.MANUAL,
        aggregation_key="python_memory_allocations",
        subject=FindingSubject(
            pod.metadata.name,
            FindingSubjectType.TYPE_POD,
            pod.metadata.namespace,
        ),
    )

    blocks = [
        HeaderBlock("Summary"),
        MarkdownBlock(
            f"*Total unfreed allocations: {humanize.naturalsize(snapshot.total)}*"
        ),
        MarkdownBlock(
            f"*Additional overhead from tracing: {humanize.naturalsize(snapshot.overhead)}*"
        ),
        DividerBlock(),
        HeaderBlock("Largest unfreed allocations"),
    ]
    blocks.extend([MarkdownBlock(stat.to_markdown()) for stat in snapshot.data])
    blocks.append(
        MarkdownBlock(f"*Other unfreed memory:* {snapshot.other_data.to_markdown()}")
    )
    finding.add_enrichment(blocks, annotations={SlackAnnotations.ATTACHMENT: True})
    event.add_finding(finding)
