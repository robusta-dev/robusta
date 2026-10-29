import logging
from typing import Optional

from robusta.integrations.kubernetes.api_client_utils import get_namespace_labels


def resolve_tenant(key: str, namespace: Optional[str]) -> Optional[str]:
    """
    Returns the value of the `key` label of a namespace, read from the cached namespace data (NAMESPACE_DATA_TTL).
    Returns None when there is no namespace or no such label, so the caller keeps its configured default tenant.
    """
    if not namespace:
        return None
    try:
        tenant = (get_namespace_labels(namespace) or {}).get(key)
    except KeyError:  # a namespace created after the last reload, or deleted
        tenant = None
    if not tenant:
        logging.warning(f"No '{key}' label on namespace {namespace}, using the default Prometheus tenant")
    return tenant
