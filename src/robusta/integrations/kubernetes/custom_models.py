import time
from typing import Type, TypeVar, List, Dict

import hikaru
import json
import yaml
from hikaru.model import *  # *-import is necessary for hikaru subclasses to work
from pydantic import BaseModel

from ...core.model.env_vars import INSTALLATION_NAMESPACE
from .api_client_utils import *
from .templates import get_deployment_yaml

S = TypeVar("S")
T = TypeVar("T")
PYTHON_DEBUGGER_IMAGE = (
    "us-central1-docker.pkg.dev/genuine-flight-317411/devel/debug-toolkit:v4.2"
)


# TODO: import these from the python-tools project
class Process(BaseModel):
    pid: int
    exe: str
    cmdline: List[str]


class ProcessList(BaseModel):
    processes: List[Process]


def get_images(containers: List[Container]) -> Dict[str, str]:
    """
    Takes a list of containers and returns a dict mapping image name to image tag.
    """
    name_to_version = {}
    for container in containers:
        if ":" in container.image:
            image_name, image_tag = container.image.split(":", maxsplit=1)
            name_to_version[image_name] = image_tag
        else:
            name_to_version[container.image] = "<NONE>"
    return name_to_version


def extract_images(k8s_obj: HikaruDocumentBase) -> Optional[Dict[str, str]]:
    containers_paths = [
        [
            "spec",
            "template",
            "spec",
            "containers",
        ],  # deployment, replica set, daemon set, stateful set, job
        ["spec", "containers"],  # pod
    ]

    for path in containers_paths:
        try:
            containers = k8s_obj.object_at_path(path)
            if containers:
                return get_images(containers)
        except Exception:  # Path not found on object, not a real error
            pass

    # no containers found on that k8s obj
    return None


def does_daemonset_have_toleration(ds: DaemonSet, toleration_key: str) -> bool:
    return any(t.key == toleration_key for t in ds.spec.template.spec.tolerations)


def does_node_have_taint(node: Node, taint_key: str) -> bool:
    return any(t.key == taint_key for t in node.spec.taints)


class RobustaPod(Pod):
    def exec(self, shell_command: str, container: str = None) -> str:
        """Execute a command inside the pod"""
        if container is None:
            container = self.spec.containers[0].name

        return exec_shell_command(
            self.metadata.name, shell_command, self.metadata.namespace, container
        )

    def get_logs(self, container=None, previous=None, tail_lines=None) -> str:
        """
        Fetch pod logs
        """
        if container is None:
            container = self.spec.containers[0].name
        return get_pod_logs(
            self.metadata.name,
            self.metadata.namespace,
            container,
            previous,
            tail_lines,
        )

    @staticmethod
    def create_debugger_pod(
        pod_name: str, node_name: str, debug_image=PYTHON_DEBUGGER_IMAGE, debug_cmd=None
    ) -> "RobustaPod":
        """
        Creates a debugging pod with high privileges
        """
        debugger = RobustaPod(
            apiVersion="v1",
            kind="Pod",
            metadata=ObjectMeta(
                name=to_kubernetes_name(pod_name, "debug-"),
                namespace=INSTALLATION_NAMESPACE,
            ),
            spec=PodSpec(
                hostPID=True,
                nodeName=node_name,
                containers=[
                    Container(
                        name="debugger",
                        image=debug_image,
                        imagePullPolicy="Always",
                        command=prepare_pod_command(debug_cmd),
                        securityContext=SecurityContext(
                            capabilities=Capabilities(add=["SYS_PTRACE", "SYS_ADMIN"]),
                            privileged=True,
                        ),
                    )
                ],
            ),
        )
        # TODO: check the result code
        debugger = debugger.createNamespacedPod(debugger.metadata.namespace).obj
        return debugger

    @staticmethod
    def exec_on_node(pod_name: str, node_name: str, cmd):
        node_runner = RobustaPod.create_debugger_pod(pod_name, node_name)
        try:
            node_runner.exec(f"nsenter -t 1 -a {cmd}")
        finally:
            node_runner.delete()

    @staticmethod
    def exec_in_debugger_pod(
        pod_name: str, node_name: str, cmd, debug_image=PYTHON_DEBUGGER_IMAGE
    ) -> str:
        debugger = RobustaPod.create_debugger_pod(pod_name, node_name, debug_image)
        try:
            return debugger.exec(cmd)
        finally:
            RobustaPod.deleteNamespacedPod(
                debugger.metadata.name, debugger.metadata.namespace
            )

    def get_processes(self) -> List[Process]:
        output = RobustaPod.exec_in_debugger_pod(
            self.metadata.name,
            self.spec.nodeName,
            f"debug-toolkit pod-ps {self.metadata.uid}",
        )
        processes = ProcessList(**json.loads(output))
        return processes.processes

    def get_images(self) -> Dict[str, str]:
        return get_images(self.spec.containers)

    def has_direct_owner(self, owner_uid) -> bool:
        for owner in self.metadata.ownerReferences:
            if owner.uid == owner_uid:
                return True
        return False

    def has_toleration(self, toleration_key):
        return any(
            toleration_key == toleration.key for toleration in self.spec.tolerations
        )

    def has_cpu_limit(self) -> bool:
        for container in self.spec.containers:
            if container.resources and container.resources.limits.get("cpu"):
                return True
        return False

    def upload_file(self, path: str, contents: bytes, container: Optional[str] = None):
        if container is None:
            container = self.spec.containers[0].name
            logging.info(
                f"no container name given when uploading file, so choosing first container: {container}"
            )
        upload_file(
            self.metadata.name,
            path,
            contents,
            namespace=self.metadata.namespace,
            container=container,
        )

    @staticmethod
    def find_pods_with_direct_owner(
        namespace: str, owner_uid: str
    ) -> List["RobustaPod"]:
        all_pods: List["RobustaPod"] = PodList.listNamespacedPod(namespace).obj.items
        return list(filter(lambda p: p.has_direct_owner(owner_uid), all_pods))

    @staticmethod
    def find_pod(name_prefix, namespace) -> "RobustaPod":
        pods: PodList = PodList.listNamespacedPod(namespace).obj
        for pod in pods.items:
            if pod.metadata.name.startswith(name_prefix):
                # we serialize and then deserialize to work around https://github.com/haxsaw/hikaru/issues/15
                return hikaru.from_dict(pod.to_dict(), cls=RobustaPod)
        raise Exception(
            f"No pod exists in namespace '{namespace}' with name prefix '{name_prefix}'"
        )

    # TODO: replace with Hikaru Pod().read() but note that usage is slightly different as this is a staticmethod
    @staticmethod
    def read(name: str, namespace: str) -> "RobustaPod":
        """Read pod definition from the API server"""
        return Pod.readNamespacedPod(name, namespace).obj


class RobustaDeployment(Deployment):
    @classmethod
    def from_image(cls: Type[T], name, image="busybox", cmd=None) -> T:
        obj: RobustaDeployment = hikaru.from_dict(
            yaml.safe_load(get_deployment_yaml(name, image)), RobustaDeployment
        )
        obj.spec.template.spec.containers[0].command = prepare_pod_command(cmd)
        return obj

    def get_images(self) -> Dict[str, str]:
        return get_images(self.spec.template.spec.containers)


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

    @classmethod
    def run_simple_job_spec(cls, spec, name, timeout) -> str:
        job = RobustaJob(
            metadata=ObjectMeta(
                namespace=INSTALLATION_NAMESPACE, name=to_kubernetes_name(name)
            ),
            spec=JobSpec(
                backoffLimit=0,
                template=PodTemplateSpec(
                    spec=spec,
                ),
            ),
        )
        try:
            job = job.createNamespacedJob(job.metadata.namespace).obj
            job = hikaru.from_dict(
                job.to_dict(), cls=RobustaJob
            )  # temporary workaround for hikaru bug #15
            job: RobustaJob = wait_until_job_complete(job, timeout)
            job = hikaru.from_dict(
                job.to_dict(), cls=RobustaJob
            )  # temporary workaround for hikaru bug #15
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
hikaru.register_version_kind_class(
    RobustaDeployment, Deployment.apiVersion, Deployment.kind
)
hikaru.register_version_kind_class(RobustaJob, Job.apiVersion, Job.kind)
