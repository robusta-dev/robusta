import logging
from typing import Dict, Optional, Tuple

from robusta.core.reporting.base import Finding
from robusta.core.sinks.common.channel_transformer import ChannelTransformer
from robusta.integrations.kubernetes.api_client_utils import get_namespace_annotations, get_namespace_labels

# Sentinel passed as default_channel to ChannelTransformer.template() so we can detect
# the "any token missing" case from the outside. ChannelTransformer returns the default
# we pass in only when the override is empty (we filter that case ourselves) or when a
# referenced label/annotation key is missing — both of which we treat as unresolved here.
_UNRESOLVED = "__robusta_destination_unresolved__"


def resolve_destination_override(
    finding: Finding,
    cluster_name: str,
    default_destination: str,
    destination_override: Optional[str],
    namespace_destination_override: Optional[str],
    send_to_default_if_missing: bool,
) -> Optional[str]:
    """Pick the destination (room, channel, ...) for a finding.

    Evaluated in order:
    1. namespace_destination_override, resolved against the finding namespace's labels/annotations
    2. destination_override, resolved against the finding subject's labels/annotations
    3. default_destination, or None (drop) when an override is configured, didn't resolve,
       and send_to_default_if_missing is False
    """
    if namespace_destination_override and finding.subject.namespace:
        ns_labels, ns_annotations = _get_namespace_metadata(finding.subject.namespace)
        resolved = ChannelTransformer.template(
            namespace_destination_override,
            _UNRESOLVED,
            cluster_name,
            ns_labels,
            ns_annotations,
        )
        if resolved != _UNRESOLVED:
            return resolved

    if destination_override:
        resolved = ChannelTransformer.template(
            destination_override,
            _UNRESOLVED,
            cluster_name,
            finding.subject.labels or {},
            finding.subject.annotations or {},
        )
        if resolved != _UNRESOLVED:
            return resolved

    if not destination_override and not namespace_destination_override:
        return default_destination

    return default_destination if send_to_default_if_missing else None


def _get_namespace_metadata(namespace: str) -> Tuple[Dict[str, str], Dict[str, str]]:
    try:
        labels = get_namespace_labels(namespace) or {}
        annotations = get_namespace_annotations(namespace) or {}
    except KeyError:
        logging.debug("namespace %s not found in cache", namespace)
        return {}, {}
    return labels, annotations
