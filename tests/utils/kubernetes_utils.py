import textwrap
import uuid
from hikaru.model import Deployment


def get_crashing_deployment() -> Deployment:
    random_id = str(uuid.uuid4())
    yaml = textwrap.dedent(
        f"""\
        apiVersion: apps/v1
        kind: Deployment
        metadata:
          name: {random_id}
          namespace: robusta
        spec:
          replicas:
          selector:
            matchLabels:
              app: crashpod
          template:
            metadata:
              labels:
                app: crashpod
            spec:
              containers:
              - image: busybox
                command: ["/bin/sh"]
                args: ["-c", "echo 'going to crash. This is the crash log'; exit 125"]
                imagePullPolicy: IfNotPresent
                name: crashpod
              restartPolicy: Always
            """
    )
    return Deployment.from_yaml(yaml)
