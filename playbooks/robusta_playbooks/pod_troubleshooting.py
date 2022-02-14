# TODO: move the python playbooks into their own subpackage and put each playbook in it's own file
import humanize
from robusta.api import *
from robusta.integrations.kubernetes.process_utils import ProcessFinder, ProcessType
from robusta.utils.parsing import load_json
from typing import List


class StartProfilingParams(ActionParams):
    """
    :var seconds: Profiling duration.
    :var process_name: Profiled process name prefix.
    :var include_idle: Include idle threads
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
    Fetch the list of running processes in a pod.
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


class MemoryTraceParams(ProcessParams):
    """
    :var seconds: Memory allocations analysis duration.
    """

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
    Monitor a Python process for X seconds and show memory that was allocated and not freed.

    Use this to track memory leaks in your Python application on Kubernetes.
    """
    pod = event.get_pod()
    if not pod:
        logging.info(f"python_memory - pod not found for event: {event}")
        return

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
    event.add_finding(finding)
    process_finder = ProcessFinder(pod, params, ProcessType.PYTHON)
    process = process_finder.get_match_or_report_error(
        finding, "Profile", python_memory, python_process_inspector
    )
    if process is None:
        return

    cmd = f"debug-toolkit memory --seconds={params.seconds} {process.pid}"
    output = RobustaPod.exec_in_debugger_pod(pod.metadata.name, pod.spec.nodeName, cmd)
    snapshot = PythonMemorySnapshot(**load_json(output))

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


class DebuggerParams(ProcessParams):
    """
    :var port: debugging port.
    """

    port: int = 5678


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

@action
def debugger_stack_trace(event: PodEvent, params: DebuggerParams):
    """
    Prints a stack track of a python process and child threads

    Create a finding with the stack trace results.
    """
    pod = event.get_pod()
    if not pod:
        logging.info(f"debugger_stack_trace - pod not found for event: {event}")
        return

    process_finder = ProcessFinder(pod, params, ProcessType.PYTHON)
    pid = process_finder.get_lowest_relevant_pid()

    if not pid:
        logging.info(f"debugger_stack_trace - no relevant pids")

    # if params pid is set, this will be returned, if not we return the parent process
    finding = Finding(
        title=f"Stacktrace on pid {pid}:",
        source=FindingSource.MANUAL,
        aggregation_key="debugger_stack_trace",
        subject=FindingSubject(
            pod.metadata.name,
            FindingSubjectType.TYPE_POD,
            pod.metadata.namespace,
        ),
    )
    event.add_finding(finding)
    cmd = f"debug-toolkit stack-trace {pid}"
    output = RobustaPod.exec_in_debugger_pod(
            pod.metadata.name,
            pod.spec.nodeName,
            cmd,
        )
    blocks =[]
    for thread_output in output.split('\n\n'):
        if thread_output.startswith('Current thread'):
            # this is the thread we are getting the stack trace from, not relevant for debugging
            continue
        if thread_output:
            blocks.append(MarkdownBlock(f"```\n{thread_output}\n```"))
    finding.add_enrichment(blocks, annotations={SlackAnnotations.ATTACHMENT: True})


@action
def python_process_inspector(event: PodEvent, params: DebuggerParams):
    """

    Create a finding with alternative debugging options for received processes ; i.e. Stack-trace or Memory-trace.

    """
    pod = event.get_pod()
    if not pod:
        logging.info(f"advanced_debugging_options - pod not found for event: {event}")
        return
    finding = Finding(
        title=f"Advanced debugging for pod {pod.metadata.name} in namespace {pod.metadata.namespace}:",
        source=FindingSource.MANUAL,
        aggregation_key="python_process_inspector",
        subject=FindingSubject(
            pod.metadata.name,
            FindingSubjectType.TYPE_POD,
            pod.metadata.namespace,
        ),
    )
    event.add_finding(finding)

    process_finder = ProcessFinder(pod, params, ProcessType.PYTHON)
    relevant_processes_pids = process_finder.get_pids()
    if not relevant_processes_pids :
        ERROR_MESSAGE = f"No relevant processes found for advanced debugging."
        logging.info(ERROR_MESSAGE)
        finding.add_enrichment(
            [MarkdownBlock(ERROR_MESSAGE)]
        )
        return

    finding.add_enrichment(
        [MarkdownBlock(f"Please select an advanced debugging choice:")]
    )
    if params.interactive:
        choices = {}
        for proc_pid in relevant_processes_pids:
            updated_params = params.copy()
            updated_params.process_substring = ""
            updated_params.pid = proc_pid
            choices[f"StackTrace {updated_params.pid}"] = CallbackChoice(
                action=debugger_stack_trace,
                action_params=updated_params,
                kubernetes_object=pod,
            )
        finding.add_enrichment([CallbackBlock(choices),
                                MarkdownBlock(
                                    "*After clicking a button please wait up to 120 seconds for a response*"
                                )
                                ])


@action
def python_debugger(event: PodEvent, params: DebuggerParams):
    """
    Attach a python debugger to a running pod. No need to modify the application's code or restart it.

    Steps:
        1. :ref:`Install Robusta <Installation Guide>`
        2. Manually trigger this action using the Robusta CLI and the pod's name:

        .. code-block:: bash

             robusta playbooks trigger python_debugger name=podname namespace=default

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

    process_finder = ProcessFinder(pod, params, ProcessType.PYTHON)
    process = process_finder.get_match_or_report_error(finding, "Debug", python_memory, python_process_inspector)
    if process is None:
        return

    cmd = f"debug-toolkit debugger {process.pid} --port {params.port}"
    output = load_json(
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
