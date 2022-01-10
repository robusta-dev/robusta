# TODO: move the python playbooks into their own subpackage and put each playbook in it's own file
import json
import textwrap
import humanize
from robusta.api import *
from typing import List


class StartProfilingParams(ActionParams):
    """
    :var seconds: Profiling duration.
    :var process_name: Profiled process name prefix.
    :var include_idle: Inclide idle threads
    """

    seconds: int = 2
    process_name: str = ""
    include_idle: bool = False


@action
def python_profiler(event: PodEvent, action_params: StartProfilingParams):
    """
    Attach a python profiler to a running pod, and run a profiling session for the specified duration.

    No need to change the profiled application code, or to restart it.

    This is powered by PySpy
    """
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
    """
    Create a finding with the list of running processes on the pod.
    """
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


class MemoryTraceParams(ActionParams):
    """
    :var seconds: Memory allocations analysis duration.
    :var process_substring: Inspected process name prefix.
    """

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
    """
    Analyze memory allocation on the specified python process, for the specified duration.

    Create a finding with the memory analysis results.
    """
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


class DebuggerParams(ActionParams):
    """
    :var process_substring: Debugged process name prefix.
    :var pid: Process id of the target process.
    :var port: Debugging port.
    :var interactive: If more than one process is matched, interactively ask which process to debug via Slack. Note that you won't receive immediate output in Slack after clicking a button. It takes about 30-60 seconds for the playbook to finish running.
    """

    process_substring: str = ""
    pid: int = None
    port: int = 5678
    interactive: bool = True


def get_example_launch_json(params: DebuggerParams):
    return {
        "version": "0.2.0",
        "configurations": [
            {
                "name": "Python: Remote Attach",
                "type": "python",
                "request": "attach",
                "connect": {"host": "localhost", "port": params.port},
                "justMyCode": False,
                "pathMappings": [
                    {
                        "localRoot": "/local/path/to/module/root",
                        "remoteRoot": "/remote/path/to/same/module",
                    },
                ],
            }
        ],
    }


def get_loaded_module_info(data):
    modules = data["loaded_modules"]
    max_indent = min(40, max(len(name) for name in modules.keys()))

    output = ""
    for name in sorted(modules.keys()):
        path = modules[name]
        indentation = " " * max(0, max_indent - len(name))
        output += f"{name}:{indentation}{path}\n"

    return (
        textwrap.dedent(
            f"""\
        These are the remote module paths
        
        Use this list to guess the right value for `remoteRoot` in launch.json
        
        When setting breakpoints, VSCode determines the remote filename by replacing `localRoot` with `remoteRoot` in the filename  
        %s"""
        )
        % (output,)
    )


def get_debugger_warnings(data):
    message = data["message"]
    if message.strip().lower() == "success":
        return None
    return message


def get_relevant_processes(all_processes: List[Process], params: DebuggerParams):
    pid_to_process = {p.pid: p for p in all_processes}

    if params.pid is None:
        return [
            p
            for p in pid_to_process.values()
            if "python" in p.exe and params.process_substring in " ".join(p.cmdline)
        ]

    if params.pid not in pid_to_process:
        return []

    return [pid_to_process[params.pid]]


def get_process_blocks(
    processes: List[Process], pod: RobustaPod, params: DebuggerParams
) -> List[BaseBlock]:
    blocks = [
        TableBlock(
            [[p.pid, p.exe, " ".join(p.cmdline)] for p in processes],
            ["pid", "exe", "cmdline"],
        ),
    ]
    # we don't enable this by default because it is bad UX. if you press a callback buttons then nothing
    # seems to happen for 60 seconds while the playbook runs
    if params.interactive:
        choices = {}
        for proc in processes:
            updated_params = params.copy()
            updated_params.process_substring = ""
            updated_params.pid = proc.pid
            choices[f"Debug {proc.pid}"] = CallbackChoice(
                action=python_debugger,
                action_params=updated_params,
                kubernetes_object=pod,
            )
        blocks.append(CallbackBlock(choices))
        blocks.append(
            MarkdownBlock(
                "*After clicking a button please wait up to 120 seconds for a response*"
            )
        )
    return blocks


@action
def python_debugger(event: PodEvent, params: DebuggerParams):
    """
    Attach a python debugger to a running pod. No need to modify the application's code or restart it.

    Steps:
        1. :ref:`Install Robusta <Installation Guide>`
        2. Manually trigger this action using the Robusta CLI and the pod's name:

        .. code-block:: bash

             robusta playbooks trigger python_debugger name=myapp namespace=default

        2. Follow the instructions you receive and run `kubectl port-forward`
        3. In Visual Studio Code do a Remote Attach as per the instructions

    Now you can use break points and log points in VSCode.
    """
    pod = event.get_pod()
    if not pod:
        logging.info(f"python_debugger - pod not found for event: {event}")
        return

    finding = Finding(
        title=f"Python debugging session on pod {pod.metadata.name} in namespace {pod.metadata.namespace}:",
        source=FindingSource.MANUAL,
        aggregation_key="python_debugger",
        subject=FindingSubject(
            pod.metadata.name,
            FindingSubjectType.TYPE_POD,
            pod.metadata.namespace,
        ),
    )
    event.add_finding(finding)

    all_processes = pod.get_processes()
    relevant_processes = get_relevant_processes(all_processes, params)
    if len(relevant_processes) == 0:
        finding.add_enrichment(
            [MarkdownBlock(f"No matching processes. The processes in the pod are:")]
            + get_process_blocks(all_processes, pod, params)
        )
        return
    elif len(relevant_processes) > 1:
        finding.add_enrichment(
            [
                MarkdownBlock(
                    f"More than one matching process. The matching processes are:"
                )
            ]
            + get_process_blocks(relevant_processes, pod, params)
        )
        return

    # we have exactly one process to debug
    pid = relevant_processes[0].pid
    cmd = f"debug-toolkit debugger {pid} --port {params.port}"
    output = json.loads(
        RobustaPod.exec_in_debugger_pod(
            pod.metadata.name,
            pod.spec.nodeName,
            cmd,
        )
    )
    finding.add_enrichment(
        [
            MarkdownBlock(
                f"""
                1. Run: `kubectl port-forward -n {pod.metadata.namespace} {pod.metadata.name} {params.port}:{params.port}`
                2. In VSCode do a Remote Attach to `localhost` and port {params.port}
                3. If breakpoints don't work in VSCode you will need to set `pathMappings` in launch.json. See attached files for assistance.
                4. Use VSCode logpoints to debug without pausing your application. Happy debugging!
                """,
                dedent=True,
            )
        ]
    )

    warnings = get_debugger_warnings(output)
    if warnings is not None:
        finding.add_enrichment([HeaderBlock("Warning"), MarkdownBlock(warnings)])

    finding.add_enrichment(
        [
            FileBlock(
                "launch.json",
                json.dumps(get_example_launch_json(params), indent=4).encode(),
            ),
            FileBlock("loaded-modules.txt", get_loaded_module_info(output).encode()),
        ]
    )
    logging.info(
        "Done! See instructions for connecting to the debugger in Slack or Robusta UI"
    )
