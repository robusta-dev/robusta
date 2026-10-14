from typing import Optional

from pydantic.v1 import SecretStr, validator

from robusta.core.sinks.common.channel_transformer import ChannelTransformer
from robusta.core.sinks.sink_base_params import SinkBaseParams
from robusta.core.sinks.sink_config import SinkConfigBase
from robusta.integrations.msteams.graph.graph_client import DEFAULT_AUTHORITY_HOST, DEFAULT_GRAPH_ENDPOINT


class MsTeamsGraphSinkParams(SinkBaseParams):
    tenant_id: str
    client_id: str
    client_secret: Optional[SecretStr] = None
    username: str
    password: SecretStr
    # Default destination. Overrides may resolve to "<channel_id>" (in team_id) or "<team_id>/<channel_id>"
    team_id: str
    channel_id: str
    channel_override: Optional[str] = None
    namespace_channel_override: Optional[str] = None
    send_to_default_if_missing: bool = True
    disable_platform_links: bool = False
    send_files: bool = True
    oauth_scope: Optional[str] = None  # defaults to <graph_endpoint>/.default
    authority_host: str = DEFAULT_AUTHORITY_HOST
    graph_endpoint: str = DEFAULT_GRAPH_ENDPOINT

    @classmethod
    def _get_sink_type(cls):
        return "msteams_graph"

    @validator("channel_override", "namespace_channel_override")
    def validate_overrides(cls, v):
        return ChannelTransformer.validate_channel_override(v)


class MsTeamsGraphSinkConfigWrapper(SinkConfigBase):
    ms_teams_graph_sink: MsTeamsGraphSinkParams

    def get_params(self) -> SinkBaseParams:
        return self.ms_teams_graph_sink
