import textwrap

from ...core.model.env_vars import INSTALLATION_NAMESPACE


def get_deployment_yaml(name, image="busybox"):
    return textwrap.dedent(
        f"""\
  apiVersion: apps/v1
  kind: Deployment
  metadata:
    name: {name}
    namespace: {INSTALLATION_NAMESPACE}
    labels:
      app: {name}
  spec:
    replicas: 1
    selector:
      matchLabels:
        app: {name}
    template:
      metadata:
        labels:
          app: {name}
      spec:
        containers:
        - name: runner
          image: {image}
          imagePullPolicy: Always
  """
    )
