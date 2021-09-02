import datetime
import logging
import os
import re
import time
import traceback
from typing import List, Optional

from kubernetes import config
from kubernetes.client.api import core_v1_api
from kubernetes.client.rest import ApiException
from kubernetes.stream import stream

from hikaru.model import Job

RUNNING_STATE = "Running"

try:
    if os.getenv("KUBERNETES_SERVICE_HOST"):
        config.load_incluster_config()
    else:
        config.load_kube_config()
except config.config_exception.ConfigException as e:
    logging.warning(f"Running without kube-config! e={e}")


core_v1 = core_v1_api.CoreV1Api()

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


def exec_shell_command(name, shell_command: str, namespace="default", container=""):
    commands = default_exec_command.copy()
    commands.append(shell_command)
    return exec_commands(name, commands, namespace, container)


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
        resp = core_v1.read_namespaced_pod_log(
            name,
            namespace,
            container=container,
            previous=previous,
            tail_lines=tail_lines,
            since_seconds=since_seconds,
        )

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


def exec_commands(name, exec_command, namespace="default", container=""):
    logging.debug(
        f"Executing command name: {name} command: {exec_command} namespace: {namespace} container: {container}"
    )
    resp = None

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

    try:
        resp = stream(
            core_v1.connect_get_namespaced_pod_exec,
            name,
            namespace,
            container=container,
            command=exec_command,
            stderr=True,
            stdin=False,
            stdout=True,
            tty=False,
        )

    except ApiException as e:
        if e.status != 404:
            logging.exception(f"exec command {exec_command} resulted with error")
            resp = "error executing commands"

    logging.debug(f"exec command response {resp}")
    return resp


def to_kubernetes_name(name, prefix=""):
    """
    returns a valid and unique kubernetes name based on prefix and name, replacing characters in name as necessary
    see https://kubernetes.io/docs/concepts/overview/working-with-objects/names/
    """
    unique_id = str(time.time()).replace(".", "-")
    safe_name = re.sub("[^0-9a-zA-Z\\-]+", "-", name)
    return f"{prefix}{safe_name}-{unique_id}"[:63]


def parse_kubernetes_datetime(k8s_datetime: str) -> datetime.datetime:
    return datetime.datetime.strptime(k8s_datetime, "%Y-%m-%dT%H:%M:%S%z")


def parse_kubernetes_datetime_to_ms(k8s_datetime: str) -> float:
    return parse_kubernetes_datetime(k8s_datetime).timestamp() * 1000
