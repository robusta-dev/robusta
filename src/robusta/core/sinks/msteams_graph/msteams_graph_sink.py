import logging
from typing import Optional, Tuple

from robusta.core.reporting import Finding
from robusta.core.sinks.common.destination_override import resolve_destination_override
from robusta.core.sinks.msteams_graph.msteams_graph_sink_params import MsTeamsGraphSinkConfigWrapper
from robusta.core.sinks.sink_base import SinkBase
from robusta.integrations.msteams.graph.graph_client import MsTeamsGraphClient
from robusta.integrations.msteams.graph.sender import MsTeamsGraphSender


class MsTeamsGraphSink(SinkBase):
    def __init__(self, sink_config: MsTeamsGraphSinkConfigWrapper, registry):
        super().__init__(sink_config.ms_teams_graph_sink, registry)
        params = sink_config.ms_teams_graph_sink

        client = MsTeamsGraphClient(
            tenant_id=params.tenant_id,
            client_id=params.client_id,
            username=params.username,
            password=params.password.get_secret_value(),
            client_secret=params.client_secret.get_secret_value() if params.client_secret else None,
            scope=params.oauth_scope,
            authority_host=params.authority_host,
            graph_endpoint=params.graph_endpoint,
        )
        self.sender = MsTeamsGraphSender(
            client=client,
            account_id=self.account_id,
            cluster_name=self.cluster_name,
            prefer_redirect_to_platform=params.prefer_redirect_to_platform,
            send_files=params.send_files,
        )

    def write_finding(self, finding: Finding, platform_enabled: bool):
        destination = self._resolve_destination(finding)
        if destination is None:
            logging.debug(f"no Teams channel resolved for {finding.title}, dropping it")
            return
        team_id, channel_id = destination
        if self.params.disable_platform_links:
            platform_enabled = False
        self.sender.send_finding(finding, platform_enabled, team_id=team_id, channel_id=channel_id)

    def _resolve_destination(self, finding: Finding) -> Optional[Tuple[str, str]]:
        channel = resolve_destination_override(
            finding,
            self.cluster_name,
            self.params.channel_id,
            self.params.channel_override,
            self.params.namespace_channel_override,
            self.params.send_to_default_if_missing,
        )
        if channel is None:
            return None
        return self.split_team_and_channel(channel.strip(), self.params.team_id)

    @staticmethod
    def split_team_and_channel(destination: str, default_team_id: str) -> Tuple[str, str]:
        # team ids are GUIDs and channel ids (19:...@thread.tacv2) never contain "/"
        if "/" in destination:
            team_id, channel_id = destination.split("/", 1)
            return team_id.strip(), channel_id.strip()
        return default_team_id, destination
