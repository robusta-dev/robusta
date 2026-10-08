from typing import Optional

from robusta.core.reporting.base import Finding
from robusta.core.sinks.common.destination_override import resolve_destination_override
from robusta.core.sinks.sink_base import SinkBase
from robusta.core.sinks.webex.webex_sink_params import WebexSinkConfigWrapper
from robusta.integrations.webex.sender import WebexSender


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
        return resolve_destination_override(
            finding,
            self.cluster_name,
            self.params.room_id,
            self.params.room_id_override,
            self.params.namespace_room_id_override,
            self.params.send_to_default_if_missing,
        )
