import uuid
from hikaru.model import *

from core.model.env_vars import INSTALLATION_NAMESPACE


def get_crashing_deployment() -> Deployment:
    return Deployment(
        metadata=ObjectMeta(name=str(uuid.uuid4()), namespace=INSTALLATION_NAMESPACE),
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
