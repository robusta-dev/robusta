from typing import Optional


def load_token() -> Optional[str]:
    # NOTE: This one will be mounted if openshift is enabled in values.yaml
    try:
        with open('/var/run/secrets/kubernetes.io/serviceaccount/token', 'r') as file:
            return file.read().strip()
    except FileNotFoundError:
        return None
