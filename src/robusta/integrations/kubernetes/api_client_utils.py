import datetime
import logging
import os
import re
import time
import traceback
import io
import tempfile
import tarfile
from typing import List, Optional

from kubernetes import config
from kubernetes.client.api import core_v1_api
from kubernetes.client.rest import ApiException
from kubernetes.stream import stream

from hikaru.model import Job

RUNNING_STATE = "Running"
SUCCEEDED_STATE = "Succeeded"

try:
    if os.getenv("KUBERNETES_SERVICE_HOST"):
        config.load_incluster_config()
    else:
        config.load_kube_config()
except config.config_exception.ConfigException as e:
    logging.warning(f"Running without kube-config! e={e}")


default_exec_command = ["/bin/sh", "-c"]


def wait_until(
    read_function, predicate_function, timeout_sec: float, backoff_wait_sec: float
):
    """
    repeatedly calls predicate_function(read_function)) until predicate_function returns True or we timeout
    return the last result of read_function() on success and raises an exception on timeout
    between attempts, we wait backoff_wait_sec seconds
    """
    start_time_sec = time.time()

    while start_time_sec + timeout_sec > time.time():
        try:
            resp = read_function()
            if predicate_function(resp):
                return resp
        except ApiException as e:
            logging.error(f"failed calling read_function {traceback.format_exc()}")

        time.sleep(backoff_wait_sec)

    raise Exception("Failed to reach wait condition")


def wait_until_job_complete(job: Job, timeout):
    """
    wait until a kubernetes Job object either succeeds or fails at least once
    """

    def is_job_complete(j: Job) -> bool:
        return j.status.completionTime is not None or j.status.failed is not None

    return wait_until(
        lambda: Job.readNamespacedJob(job.metadata.name, job.metadata.namespace).obj,
        is_job_complete,
        timeout,
        5,
    )


# TODO: refactor to use wait_until function
def wait_for_pod_status(
    name, namespace, status: str, timeout_sec: float, backoff_wait_sec: float
) -> str:
    pod_details = f"pod status: {name} {namespace} {status} {timeout_sec}"
    logging.debug(f"waiting for {pod_details}")

    start_time_sec = time.time()
    while start_time_sec + timeout_sec > time.time():
        try:
            core_v1 = core_v1_api.CoreV1Api()
            resp = core_v1.read_namespaced_pod_status(name, namespace)

            if resp.status.phase == status:
                logging.debug(f"reached {pod_details}")
                return status

        except ApiException as e:
            logging.error(
                f"failed to get pod status {name} {namespace} {traceback.format_exc()}"
            )

        time.sleep(backoff_wait_sec)

    logging.debug(f"failed to reach {pod_details}")
    return "FAIL"


def exec_shell_command(name, shell_command: str, namespace="default", container=None):
    commands = default_exec_command.copy()
    commands.append(shell_command)
    return exec_commands(name, commands, namespace, container)


def upload_file(
    name: str, destination: str, contents: bytes, namespace="default", container=None
):
    core_v1 = core_v1_api.CoreV1Api()
    resp = stream(
        core_v1.connect_get_namespaced_pod_exec,
        name,
        namespace,
        container=container,
        command=["tar", "xvf", "-", "-C", "/"],
        stderr=True,
        stdin=True,
        stdout=True,
        tty=False,
        _preload_content=False,
    )

    with tempfile.TemporaryFile() as local_tar_file:
        with tarfile.open(fileobj=local_tar_file, mode="w") as tar:
            tarinfo = tarfile.TarInfo(destination)
            tarinfo.size = len(contents)
            tar.addfile(tarinfo, fileobj=io.BytesIO(contents))

        local_tar_file.seek(0)
        resp.write_stdin(local_tar_file.read())

        while resp.is_open():
            resp.update(timeout=1)
            if resp.peek_stdout():
                print("STDOUT: %s" % resp.read_stdout())
            if resp.peek_stderr():
                print("STDERR: %s" % resp.read_stderr())
            else:
                break
        resp.close()


def get_pod_logs(
    name,
    namespace="default",
    container="",
    previous=None,
    tail_lines=None,
    since_seconds=None,
):
    resp = None
    try:
        core_v1 = core_v1_api.CoreV1Api()
        resp = core_v1.read_namespaced_pod_log(
            name,
            namespace,
            container=container,
            previous=previous,
            tail_lines=tail_lines,
            since_seconds=since_seconds,
            _preload_content=False  # If this flag is not used, double quotes in json objects in stdout are converted
            # by the kubernetes client to single quotes, which makes json.loads() fail.
            # We therefore use this flag in order to get the raw bytes and decode the output
        ).data.decode("utf-8")

    except ApiException as e:
        if e.status != 404:
            logging.exception(f"failed to get pod logs {name} {namespace} {container}")
            resp = ""

    logging.debug(f"get logs {resp}")
    return resp


def prepare_pod_command(cmd) -> Optional[List[str]]:
    if type(cmd) == list:
        return cmd
    elif type(cmd) == str:
        return cmd.split(" ")  # cmd need to be a list of strings
    elif cmd is None:
        return None
    else:
        logging.exception(f"cmd {cmd} has unknown type {type(cmd)}")
        return cmd


def exec_commands(name, exec_command, namespace="default", container=None):
    logging.debug(
        f"Executing command name: {name} command: {exec_command} namespace: {namespace} container: {container}"
    )
    response_stdout = None

    # verify pod state before connecting
    pod_status = wait_for_pod_status(
        name, namespace, RUNNING_STATE, 90, 0.2
    )  # TODO config
    if pod_status != RUNNING_STATE:
        msg = (
            f"Not running exec commands. Pod {name} {namespace} is not in running state"
        )
        logging.error(msg)
        return msg

    wsclient = None
    try:
        core_v1 = core_v1_api.CoreV1Api()
        wsclient = stream(
            core_v1.connect_get_namespaced_pod_exec,
            name,
            namespace,
            container=container,
            command=exec_command,
            stderr=True,
            stdin=False,
            stdout=True,
            tty=False,
            _preload_content=False,  # fix https://github.com/kubernetes-client/python/issues/811
        )
        wsclient.run_forever()
        response = wsclient.read_all()
        logging.debug(f"exec command response {response}")
    finally:
        if wsclient is not None:
            wsclient.close()

    return response


def to_kubernetes_name(name, prefix=""):
    """
    Returns a valid and unique kubernetes name based on prefix and name, replacing characters in name as necessary
    see https://kubernetes.io/docs/concepts/overview/working-with-objects/names/
    """
    unique_id = str(time.time()).replace(".", "-")
    safe_name = re.sub("[^0-9a-zA-Z\\-]+", "-", name)
    return f"{prefix}{safe_name}-{unique_id}"[:63]


def parse_kubernetes_datetime(k8s_datetime: str) -> datetime.datetime:
    """
    Parse a date/time related field in a Kubernetes object and convert it from string to a python datetime object
    """
    return datetime.datetime.strptime(k8s_datetime, "%Y-%m-%dT%H:%M:%S%z")


def parse_kubernetes_datetime_with_ms(k8s_datetime: str) -> datetime.datetime:
    return datetime.datetime.strptime(k8s_datetime, "%Y-%m-%dT%H:%M:%S.%f%z")


def parse_kubernetes_datetime_to_ms(k8s_datetime: str) -> float:
    """
        for timestamps eventTime has milliseconds and firstTimestamp,lastTimestamp,creationTimestamp do not.
        we parse the more commonly used timestamp first
    """
    try:
        return parse_kubernetes_datetime(k8s_datetime).timestamp() * 1000
    except:
        return parse_kubernetes_datetime_with_ms(k8s_datetime).timestamp() * 1000
