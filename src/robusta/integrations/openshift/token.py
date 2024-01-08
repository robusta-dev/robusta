from typing import Optional

from robusta.core.model.env_vars import IS_OPENSHIFT

# NOTE: This one will be mounted if openshift is enabled in values.yaml
TOKEN_LOCATION = '/var/run/secrets/kubernetes.io/serviceaccount/token'


def load_token() -> Optional[str]:
    if not IS_OPENSHIFT:
        return None

    try:
        with open(TOKEN_LOCATION, 'r') as file:
            return file.read()
    except FileNotFoundError:
        return None
