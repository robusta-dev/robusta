import uuid
from hikaru.model import *


def get_crashing_deployment(namespace: str) -> Deployment:
    return Deployment(
        metadata=ObjectMeta(name=str(uuid.uuid4()), namespace=namespace),
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
