# playbooks for peeking inside running pods
import textwrap
import humanize
from robusta.api import *
from typing import List


class StartProfilingParams(BaseModel):
    namespace: str = "default"
    seconds: int = 2
    process_name: str = ""
    pod_name: str


@action
def python_profiler(event: ExecutionBaseEvent, action_params: StartProfilingParams):
    # This should use ephemeral containers, but they aren't in GA yet. To enable them on GCP for example,
    # you need to create a brand new cluster. Therefore we're sticking with regular containers for now
    pod = RobustaPod.find_pod(action_params.pod_name, action_params.namespace)
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

        for proc in processes:
            cmd = " ".join(proc.cmdline)
            if action_params.process_name not in cmd:
                logging.info(
                    f"skipping process because it doesn't match process_name. {cmd}"
                )
                continue
            elif "python" not in proc.exe:
                logging.info(
                    f"skipping process because it doesn't look like a python process. {cmd}"
                )
                continue

            filename = "/profile.svg"
            pyspy_output = debugger.exec(
                f"py-spy record --duration={action_params.seconds} --pid={proc.pid} --rate 30 --nonblocking -o {filename}"
            )
            if "Error:" in pyspy_output:
                continue

            svg = debugger.exec(f"cat {filename}")
            finding.add_enrichment([FileBlock(f"{cmd}.svg", svg)])
        event.add_finding(finding)

    finally:
        debugger.deleteNamespacedPod(
            debugger.metadata.name, debugger.metadata.namespace
        )


class PodInfoParams(BaseModel):
    pod_name: str
    namespace: str = "default"


@action
def pod_ps(event: ExecutionBaseEvent, action_params: PodInfoParams):
    logging.info(f"getting info for: {action_params}")

    pod: RobustaPod = RobustaPod.find_pod(
        action_params.pod_name, action_params.namespace
    )
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
                [[proc.pid, proc.exe, proc.cmdline] for proc in processes],
                ["pid", "exe", "cmdline"],
            )
        ]
    )
    event.add_finding(finding)


class MemoryTraceParams(PodParams):
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
def python_memory(event: ExecutionBaseEvent, params: MemoryTraceParams):
    pod: RobustaPod = RobustaPod.find_pod(params.pod_name, params.pod_namespace)
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
        HeaderBlock("Largest unfreed allocations"),
        DividerBlock(),
    ]
    blocks.extend([MarkdownBlock(stat.to_markdown()) for stat in snapshot.data])
    blocks.append(
        MarkdownBlock(f"*Other unfreed memory:* {snapshot.other_data.to_markdown()}")
    )
    finding.add_enrichment(blocks, annotations={SlackAnnotations.ATTACHMENT: True})
    event.add_finding(finding)
