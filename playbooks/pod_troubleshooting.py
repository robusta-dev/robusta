# playbooks for peeking inside running pods
from cairosvg import svg2png

from robusta.api import *


class StartProfilingParams(BaseModel):
    namespace: str = "default"
    seconds: int = 2
    process_name: str = ""
    slack_channel: str
    pod_name: str


@on_manual_trigger
def python_profiler(event: ManualTriggerEvent):
    # This should use ephemeral containers, but they aren't in GA yet. To enable them on GCP for example,
    # you need to create a brand new cluster. Therefore we're sticking with regular containers for now
    action_params = StartProfilingParams(**event.data)
    pod = RobustaPod.find_pod(action_params.pod_name, action_params.namespace)
    processes = pod.get_processes()

    debugger = pod.create_debugger_pod()

    try:
        for proc in processes:
            cmd = " ".join(proc.cmdline)
            if action_params.process_name not in cmd:
                logging.info(f"skipping process because it doesn't match process_name. {cmd}")
                continue
            elif "python" not in proc.exe:
                logging.info(f"skipping process because it doesn't look like a python process. {cmd}")
                continue

            filename = "/profile.svg"
            pyspy_output = debugger.exec(f"py-spy record --duration={action_params.seconds} --pid={proc.pid} --rate 30 --nonblocking -o {filename}")
            if "Error:" in pyspy_output:
                continue

            svg = debugger.exec(f"cat {filename}")
            event.report_blocks.append(FileBlock(f"{cmd}.svg", svg))

        event.slack_channel = action_params.slack_channel
        event.report_title = f"Profile results for {pod.metadata.name} in namespace {pod.metadata.namespace}:"
        send_to_slack(event)
    finally:
        debugger.deleteNamespacedPod(debugger.metadata.name, debugger.metadata.namespace)


class PodInfoParams(BaseModel):
    pod_name: str
    namespace: str = "default"


@on_manual_trigger
def pod_ps(event: ManualTriggerEvent):
    action_params = PodInfoParams(**event.data)
    logging.info(f"getting info for: {action_params}")

    pod: RobustaPod = RobustaPod.find_pod(action_params.pod_name, action_params.namespace)
    for proc in pod.get_processes():
        print(f"{proc.pid}\t{proc.exe}\t{proc.cmdline}")


class PythonStackDumpParams(BaseModel):
    namespace: str = "default"
    process_name: str = ""
    slack_channel: str
    pod_name: str

