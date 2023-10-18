import json
import logging
import re
import time
from enum import Enum, auto
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple, Type, TypeVar

import hikaru
import yaml
from hikaru.model.rel_1_26 import *  # * import is necessary for hikaru subclasses to work
from kubernetes.client import ApiException
from pydantic import BaseModel

from robusta.core.model.env_vars import IMAGE_REGISTRY, INSTALLATION_NAMESPACE, RELEASE_NAME
from robusta.integrations.kubernetes.api_client_utils import (
    SUCCEEDED_STATE,
    exec_shell_command,
    get_pod_logs,
    prepare_pod_command,
    to_kubernetes_name,
    upload_file,
    wait_for_pod_status,
    wait_until_job_complete,
)
from robusta.integrations.kubernetes.templates import get_deployment_yaml
from robusta.utils.parsing import load_json

if TYPE_CHECKING:
    from src.robusta.core.model.base_params import NamedRegexPattern

S = TypeVar("S")
T = TypeVar("T")


# TODO: import these from the python-tools project
PYTHON_DEBUGGER_IMAGE = f"{IMAGE_REGISTRY}/debug-toolkit:v5.0"
JAVA_DEBUGGER_IMAGE = f"{IMAGE_REGISTRY}/java-toolkit-11:jattach"


class Process(BaseModel):
    pid: int
    exe: str
    cmdline: List[str]


class ProcessList(BaseModel):
    processes: List[Process]


def _get_match_expression_filter(expression: LabelSelectorRequirement) -> str:
    if expression.operator.lower() == "exists":
        return expression.key
    elif expression.operator.lower() == "doesnotexist":
        return f"!{expression.key}"

    values = ",".join(expression.values)
    return f"{expression.key} {expression.operator} ({values})"


def build_selector_query(selector: LabelSelector) -> str:
    label_filters = [f"{label[0]}={label[1]}" for label in selector.matchLabels.items()]
    label_filters.extend([_get_match_expression_filter(expression) for expression in selector.matchExpressions])
    return ",".join(label_filters)


def list_pods_using_selector(namespace: str, selector: LabelSelector, field_selector: str = None) -> List[Pod]:
    labels_selector = build_selector_query(selector)
    return PodList.listNamespacedPod(
        namespace=namespace,
        label_selector=labels_selector,
        field_selector=field_selector,
    ).obj.items


def _get_image_name_and_tag(image: str) -> Tuple[str, str]:
    if ":" in image:
        image_name, image_tag = image.split(":", maxsplit=1)
        return image_name, image_tag
    else:
        return image, "<NONE>"


def get_images(containers: List[Container]) -> Dict[str, str]:
    """
    Takes a list of containers and returns a dict mapping image name to image tag.
    """
    name_to_version = {}
    for container in containers:
        image_name, tag = _get_image_name_and_tag(container.image)
        name_to_version[image_name] = tag
    return name_to_version


def extract_images(k8s_obj: HikaruDocumentBase) -> Optional[Dict[str, str]]:
    images = extract_image_list(k8s_obj)
    if not images:
        # no containers found on that k8s obj
        return None

    name_to_version = {}
    for image in images:
        image_name, tag = _get_image_name_and_tag(image)
        name_to_version[image_name] = tag
    return name_to_version


def extract_image_list(k8s_obj: HikaruDocumentBase) -> List[str]:
    containers_paths = [
        [
            "spec",
            "template",
            "spec",
            "containers",
        ],  # deployment, replica set, daemon set, stateful set, job
        ["spec", "containers"],  # pod
    ]
    images = []
    for path in containers_paths:
        try:
            for container in k8s_obj.object_at_path(path):
                images.append(container.image)
        except Exception:  # Path not found on object, not a real error
            pass

    return images


def does_daemonset_have_toleration(ds: DaemonSet, toleration_key: str) -> bool:
    return any(t.key == toleration_key for t in ds.spec.template.spec.tolerations)


def does_node_have_taint(node: Node, taint_key: str) -> bool:
    return any(t.key == taint_key for t in node.spec.taints)


class RobustaEvent:
    @classmethod
    def get_events(cls, kind: str, name: str, namespace: str = None) -> EventList:
        field_selector = f"regarding.kind={kind},regarding.name={name}"
        if namespace:
            field_selector += f",regarding.namespace={namespace}"

        return EventList.listEventForAllNamespaces(field_selector=field_selector).obj


class RegexReplacementStyle(Enum):
    """
    Patterns for replacers, either asterisks "****" matching the length of the match, or the replacement name, e.g "[IP]"
    """

    SAME_LENGTH_ASTERISKS = auto()
    NAMED = auto()


class RobustaPod(Pod):
    def exec(self, shell_command: str, container: str = None) -> str:
        """Execute a command inside the pod"""
        if container is None:
            container = self.spec.containers[0].name

        return exec_shell_command(self.metadata.name, shell_command, self.metadata.namespace, container)

    def get_logs(
        self,
        container=None,
        previous=None,
        tail_lines=None,
        regex_replacer_patterns: Optional[List["NamedRegexPattern"]] = None,
        regex_replacement_style: Optional[RegexReplacementStyle] = None,
        filter_regex: Optional[str] = None,
    ) -> str:
        """
        Fetch pod logs, can replace sensitive data in the logs using a regex
        """
        if not container and self.spec.containers:
            container = self.spec.containers[0].name
        pods_logs = get_pod_logs(
            self.metadata.name,
            self.metadata.namespace,
            container,
            previous,
            tail_lines,
        )

        if pods_logs and filter_regex:
            regex = re.compile(filter_regex)
            pods_logs = "\n".join(re.findall(regex, pods_logs))

        if pods_logs and regex_replacer_patterns:
            logging.info("Sanitizing log data with the provided regex patterns")
            if regex_replacement_style == RegexReplacementStyle.NAMED:
                for replacer in regex_replacer_patterns:
                    pods_logs = re.sub(replacer.regex, f"[{replacer.name.upper()}]", pods_logs)
            else:

                def same_length_asterisks(match):
                    return "*" * len((match.group(0)))

                for replacer in regex_replacer_patterns:
                    pods_logs = re.sub(replacer.regex, same_length_asterisks, pods_logs)

        return pods_logs

    @staticmethod
    def exec_in_java_pod(
        pod_name: str,
        node_name: str,
        debug_cmd=None,
        override_jtk_image: str = JAVA_DEBUGGER_IMAGE,
        custom_annotations: Optional[Dict[str, str]] = None,
    ) -> str:
        return RobustaPod.exec_in_debugger_pod(
            pod_name, node_name, debug_cmd, debug_image=override_jtk_image, custom_annotations=custom_annotations
        )

    @staticmethod
    def create_debugger_pod(
        pod_name: str,
        node_name: str,
        debug_image=PYTHON_DEBUGGER_IMAGE,
        debug_cmd=None,
        env: Optional[List[EnvVar]] = None,
        mount_host_root: bool = False,
        custom_annotations: Optional[Dict[str, str]] = None,
    ) -> "RobustaPod":
        """
        Creates a debugging pod with high privileges
        """

        volume_mounts = None
        volumes = None
        if mount_host_root:
            volume_mounts = [VolumeMount(name="host-root", mountPath="/host")]
            volumes = [Volume(name="host-root", hostPath=HostPathVolumeSource(path="/", type="Directory"))]

        debugger = RobustaPod(
            apiVersion="v1",
            kind="Pod",
            metadata=ObjectMeta(
                name=to_kubernetes_name(pod_name, "debug-"),
                namespace=INSTALLATION_NAMESPACE,
                annotations=custom_annotations,
            ),
            spec=PodSpec(
                serviceAccountName=f"{RELEASE_NAME}-runner-service-account",
                hostPID=True,
                nodeName=node_name,
                restartPolicy="OnFailure",
                containers=[
                    Container(
                        name="debugger",
                        image=debug_image,
                        imagePullPolicy="Always",
                        command=prepare_pod_command(debug_cmd),
                        securityContext=SecurityContext(
                            capabilities=Capabilities(add=["SYS_PTRACE", "SYS_ADMIN"]), privileged=True
                        ),
                        volumeMounts=volume_mounts,
                        env=env,
                    )
                ],
                volumes=volumes,
            ),
        )
        # TODO: check the result code
        debugger = debugger.createNamespacedPod(debugger.metadata.namespace).obj
        return debugger

    @staticmethod
    def exec_on_node(pod_name: str, node_name: str, cmd, custom_annotations: Optional[Dict[str, str]] = None):
        command = f'nsenter -t 1 -a "{cmd}"'
        return RobustaPod.exec_in_debugger_pod(pod_name, node_name, command, custom_annotations=custom_annotations)

    @staticmethod
    def run_debugger_pod(
        node_name: str,
        pod_image: str,
        env: Optional[List[EnvVar]] = None,
        mount_host_root: bool = False,
        custom_annotations: Optional[Dict[str, str]] = None,
    ) -> str:
        debugger = RobustaPod.create_debugger_pod(
            node_name,
            node_name,
            pod_image,
            env=env,
            mount_host_root=mount_host_root,
            custom_annotations=custom_annotations,
        )
        try:
            pod_name = debugger.metadata.name
            pod_namespace = debugger.metadata.namespace
            pod_status = wait_for_pod_status(pod_name, pod_namespace, SUCCEEDED_STATE, 360, 0.2)
            if pod_status != SUCCEEDED_STATE:
                raise Exception(f"pod {pod_name} in {pod_namespace} failed to complete. It is in state {pod_status}")

            return debugger.get_logs()
        finally:
            RobustaPod.deleteNamespacedPod(debugger.metadata.name, debugger.metadata.namespace)

    @staticmethod
    def exec_in_debugger_pod(
        pod_name: str,
        node_name: str,
        cmd,
        debug_image=PYTHON_DEBUGGER_IMAGE,
        custom_annotations: Optional[Dict[str, str]] = None,
    ) -> str:
        debugger = RobustaPod.create_debugger_pod(
            pod_name, node_name, debug_image, custom_annotations=custom_annotations
        )
        try:
            return debugger.exec(cmd)
        finally:
            RobustaPod.deleteNamespacedPod(debugger.metadata.name, debugger.metadata.namespace)

    @staticmethod
    def extract_container_id(status: ContainerStatus) -> str:
        runtime, container_id = status.containerID.split("://")
        return container_id

    def get_processes(self, custom_annotations: Optional[Dict[str, str]] = None) -> List[Process]:
        container_ids = " ".join([self.extract_container_id(s) for s in self.status.containerStatuses])
        output = RobustaPod.exec_in_debugger_pod(
            self.metadata.name,
            self.spec.nodeName,
            f"debug-toolkit pod-ps {self.metadata.uid} {container_ids}",
            custom_annotations=custom_annotations,
        )
        processes = ProcessList(**load_json(output))
        return processes.processes

    def get_images(self) -> Dict[str, str]:
        return get_images(self.spec.containers)

    def has_direct_owner(self, owner_uid) -> bool:
        for owner in self.metadata.ownerReferences:
            if owner.uid == owner_uid:
                return True
        return False

    def has_toleration(self, toleration_key):
        return any(toleration_key == toleration.key for toleration in self.spec.tolerations)

    def has_cpu_limit(self) -> bool:
        for container in self.spec.containers:
            if container.resources and container.resources.limits.get("cpu"):
                return True
        return False

    def upload_file(self, path: str, contents: bytes, container: Optional[str] = None):
        if container is None:
            container = self.spec.containers[0].name
            logging.info(f"no container name given when uploading file, so choosing first container: {container}")
        upload_file(
            self.metadata.name,
            path,
            contents,
            namespace=self.metadata.namespace,
            container=container,
        )

    @staticmethod
    def find_pods_with_direct_owner(namespace: str, owner_uid: str) -> List["RobustaPod"]:
        all_pods: List["RobustaPod"] = PodList.listNamespacedPod(namespace).obj.items
        return list(filter(lambda p: p.has_direct_owner(owner_uid), all_pods))

    @staticmethod
    def find_pod(name_prefix, namespace) -> "RobustaPod":
        pods: PodList = PodList.listNamespacedPod(namespace).obj
        for pod in pods.items:
            if pod.metadata.name.startswith(name_prefix):
                # we serialize and then deserialize to work around https://github.com/haxsaw/hikaru/issues/15
                return hikaru.from_dict(pod.to_dict(), cls=RobustaPod)
        raise Exception(f"No pod exists in namespace '{namespace}' with name prefix '{name_prefix}'")

    # TODO: replace with Hikaru Pod().read() but note that usage is slightly different as this is a staticmethod
    @staticmethod
    def read(name: str, namespace: str) -> "RobustaPod":
        """Read pod definition from the API server"""
        return Pod.readNamespacedPod(name, namespace).obj

    @staticmethod
    def wait_for_pod_ready(pod_name: str, namespace: str, timeout: int = 60) -> "RobustaPod":
        """
        Waits for the pod to be in Running state
        """
        for _ in range(timeout):  # retry for up to timeout seconds
            try:
                pod = RobustaPod().read(pod_name, namespace)
                if pod.status.phase == "Running":
                    return pod
            except ApiException as e:
                if e.status != 404:  # re-raise the exception if it's not a NotFound error
                    raise
            time.sleep(1)
        else:
            raise RuntimeError(f"Pod {pod_name} in namespace {namespace} is not ready after {timeout} seconds")


class RobustaDeployment(Deployment):
    @classmethod
    def from_image(cls: Type[T], name, image="busybox", cmd=None) -> T:
        obj: RobustaDeployment = hikaru.from_dict(yaml.safe_load(get_deployment_yaml(name, image)), RobustaDeployment)
        obj.spec.template.spec.containers[0].command = prepare_pod_command(cmd)
        return obj

    def get_images(self) -> Dict[str, str]:
        return get_images(self.spec.template.spec.containers)

    @staticmethod
    def wait_for_deployment_ready(name: str, namespace: str, timeout: int = 60) -> "RobustaDeployment":
        """
        Waits for the deployment to be ready, i.e., the expected number of pods are running.
        """
        for _ in range(timeout):  # retry for up to timeout seconds
            try:
                deployment = RobustaDeployment().read(name, namespace)
                if deployment.status.readyReplicas == deployment.spec.replicas:
                    return deployment
            except ApiException as e:
                if e.status != 404:  # re-raise the exception if it's not a NotFound error
                    raise
            time.sleep(1)
        else:
            raise RuntimeError(f"Deployment {name} in namespace {namespace} is not ready after {timeout} seconds")


class JobSecret(BaseModel):
    name: str
    data: Dict[str, str]


class RobustaJob(Job):
    def get_pods(self) -> List[RobustaPod]:
        """
        gets the pods associated with a job
        """
        pods: PodList = PodList.listNamespacedPod(
            self.metadata.namespace, label_selector=f"job-name = {self.metadata.name}"
        ).obj
        # we serialize and then deserialize to work around https://github.com/haxsaw/hikaru/issues/15
        return [hikaru.from_dict(pod.to_dict(), cls=RobustaPod) for pod in pods.items]

    def get_single_pod(self) -> RobustaPod:
        """
        like get_pods() but verifies that only one pod is associated with the job and returns that pod
        """
        pods = self.get_pods()
        if len(pods) != 1:
            raise Exception(f"got more pods than expected for job: {pods}")
        return pods[0]

    def create_job_owned_secret(self, job_secret: JobSecret):
        """
        This secret will be auto-deleted when the pod is Terminated
        """
        # Due to inconsistant GC in K8s the OwnerReference needs to be the pod and not the job (Found in azure)
        job_pod = self.get_single_pod()
        robusta_owner_reference = OwnerReference(
            apiVersion="v1",
            kind="Pod",
            name=job_pod.metadata.name,
            uid=job_pod.metadata.uid,
            blockOwnerDeletion=False,
            controller=True,
        )
        secret = Secret(
            metadata=ObjectMeta(name=job_secret.name, ownerReferences=[robusta_owner_reference]), data=job_secret.data
        )
        try:
            return secret.createNamespacedSecret(job_pod.metadata.namespace).obj
        except Exception as e:
            logging.error(f"Failed to create secret {job_secret.name}", exc_info=True)
            raise e

    @classmethod
    def run_simple_job_spec(
        cls,
        spec,
        name,
        timeout,
        job_secret: Optional[JobSecret] = None,
        custom_annotations: Optional[Dict[str, str]] = None,
    ) -> str:
        job = RobustaJob(
            metadata=ObjectMeta(
                namespace=INSTALLATION_NAMESPACE, name=to_kubernetes_name(name), annotations=custom_annotations
            ),
            spec=JobSpec(
                backoffLimit=0,
                template=PodTemplateSpec(spec=spec, metadata=ObjectMeta(annotations=custom_annotations)),
            ),
        )
        try:
            job = job.createNamespacedJob(job.metadata.namespace).obj
            job = hikaru.from_dict(job.to_dict(), cls=RobustaJob)  # temporary workaround for hikaru bug #15
            if job_secret:
                job.create_job_owned_secret(job_secret)
            job: RobustaJob = wait_until_job_complete(job, timeout)
            job = hikaru.from_dict(job.to_dict(), cls=RobustaJob)  # temporary workaround for hikaru bug #15
            pod = job.get_single_pod()
            return pod.get_logs()
        finally:
            job.deleteNamespacedJob(
                job.metadata.name,
                job.metadata.namespace,
                propagation_policy="Foreground",
            )

    @classmethod
    def run_simple_job(cls, image, command, timeout) -> str:
        spec = PodSpec(
            containers=[
                Container(
                    name=to_kubernetes_name(image),
                    image=image,
                    command=prepare_pod_command(command),
                )
            ],
            restartPolicy="Never",
        )
        return cls.run_simple_job_spec(spec, name=image, timeout=timeout)


hikaru.register_version_kind_class(RobustaPod, Pod.apiVersion, Pod.kind)
hikaru.register_version_kind_class(RobustaDeployment, Deployment.apiVersion, Deployment.kind)
hikaru.register_version_kind_class(RobustaJob, Job.apiVersion, Job.kind)
