import uuid
from hikaru.model import *
from kubernetes.client import ApiClient


def create_crashing_deployment(api_client: ApiClient) -> Deployment:
    obj = Deployment(
        metadata=ObjectMeta(name=str(uuid.uuid4()), namespace="default"),
        spec=DeploymentSpec(
            selector=LabelSelector(matchLabels={"app": "crashpod"}),
            template=PodTemplateSpec(
                metadata=ObjectMeta(labels={"app": "crashpod"}),
                spec=PodSpec(
                    containers=[
                        Container(
                            name="crashpod",
                            image="busybox",
                            imagePullPolicy="IfNotPresent",
                            args=[
                                "-c",
                                "echo going to crash.This is the crash log"
                                "; exit 125",
                            ],
                            command=["/bin/sh"],
                        )
                    ],
                    restartPolicy="Always",
                ),
            ),
        ),
    )
    obj.client = api_client
    obj.create()
    return obj
