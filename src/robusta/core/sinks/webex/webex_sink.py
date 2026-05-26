import logging
from typing import Dict, Optional, Tuple

from robusta.core.reporting.base import Finding
from robusta.core.sinks.common.channel_transformer import ChannelTransformer
from robusta.core.sinks.sink_base import SinkBase
from robusta.core.sinks.webex.webex_sink_params import WebexSinkConfigWrapper
from robusta.integrations.kubernetes.api_client_utils import (
    get_namespace_annotations,
    get_namespace_labels,
)
from robusta.integrations.webex.sender import WebexSender

# Sentinel passed as default_channel to ChannelTransformer.template() so we can detect
# the "any token missing" case from the outside. ChannelTransformer returns the default
# we pass in only when the override is empty (we filter that case ourselves) or when a
# referenced label/annotation key is missing — both of which we treat as unresolved here.
_UNRESOLVED = "__robusta_webex_unresolved__"


class WebexSink(SinkBase):
    def __init__(self, sink_config: WebexSinkConfigWrapper, registry):
        super().__init__(sink_config.webex_sink, registry)

        self.sender = WebexSender(
            bot_access_token=sink_config.webex_sink.bot_access_token,
            room_id=sink_config.webex_sink.room_id,
            account_id=self.account_id,
            cluster_name=self.cluster_name,
            webex_params=self.params,
        )

    def write_finding(self, finding: Finding, platform_enabled: bool):
        room_id = self._resolve_room_id(finding)
        if room_id is None:
            return
        if self.params.disable_platform_links:
            platform_enabled = False
        self.sender.send_finding_to_webex(finding, platform_enabled, room_id=room_id)

    def _resolve_room_id(self, finding: Finding) -> Optional[str]:
        params = self.params

        if params.namespace_room_id_override and finding.subject.namespace:
            ns_labels, ns_annotations = self._get_namespace_metadata(finding.subject.namespace)
            resolved = ChannelTransformer.template(
                params.namespace_room_id_override,
                _UNRESOLVED,
                self.cluster_name,
                ns_labels,
                ns_annotations,
            )
            if resolved != _UNRESOLVED:
                return resolved

        if params.room_id_override:
            resolved = ChannelTransformer.template(
                params.room_id_override,
                _UNRESOLVED,
                self.cluster_name,
                finding.subject.labels or {},
                finding.subject.annotations or {},
            )
            if resolved != _UNRESOLVED:
                return resolved

        if not params.room_id_override and not params.namespace_room_id_override:
            return params.room_id

        return params.room_id if params.send_to_default_if_missing else None

    @staticmethod
    def _get_namespace_metadata(namespace: str) -> Tuple[Dict[str, str], Dict[str, str]]:
        try:
            labels = get_namespace_labels(namespace) or {}
            annotations = get_namespace_annotations(namespace) or {}
        except KeyError:
            logging.debug("namespace %s not found in cache", namespace)
            return {}, {}
        return labels, annotations
