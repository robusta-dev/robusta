import uuid

from hikaru.model.rel_1_16 import (
    Container,
    Deployment,
    DeploymentSpec,
    LabelSelector,
    ObjectMeta,
    PodSpec,
    PodTemplateSpec,
)
from kubernetes.client import ApiClient


def get_simple_deployment_obj(title: str, api_client: ApiClient = None) -> Deployment:
    obj = Deployment(
        metadata=ObjectMeta(name=str(uuid.uuid4()), namespace="default"),
        spec=DeploymentSpec(
            selector=LabelSelector(matchLabels={"app": title}),
            template=PodTemplateSpec(
                metadata=ObjectMeta(labels={"app": title}),
                spec=PodSpec(
                    containers=[
                        Container(
                            name=title,
                            image="busybox",
                            imagePullPolicy="IfNotPresent",
                            command=["/bin/sh"],
                        )
                    ],
                    restartPolicy="Always",
                ),
            ),
        ),
    )
    if api_client is not None:
        obj.client = api_client
    return obj


def create_crashing_deployment(api_client: ApiClient = None) -> Deployment:
    obj = get_simple_deployment_obj("crashpod", api_client)
    obj.spec.template.spec.containers[0].args = [
        "-c",
        "echo going to crash.This is the crash log" "; exit 125",
    ]
    obj.create()
    return obj


def create_sleeping_deployment(api_client: ApiClient = None) -> Deployment:
    obj = get_simple_deployment_obj("sleepypod", api_client)
    obj.spec.template.spec.containers[0].args = ["-c", "sleep 1000"]
    obj.create()
    return obj
