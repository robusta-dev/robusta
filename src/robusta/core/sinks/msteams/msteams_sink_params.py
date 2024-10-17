from typing import Optional

from pydantic import field_validator

from robusta.core.sinks.msteams.msteams_webhook_tranformer import MsTeamsWebhookUrlTransformer
from robusta.core.sinks.sink_base_params import SinkBaseParams
from robusta.core.sinks.sink_config import SinkConfigBase


class MsTeamsSinkParams(SinkBaseParams):
    webhook_url: str
    webhook_override: Optional[str] = None

    @classmethod
    def _get_sink_type(cls):
        return "msteams"

    @field_validator("webhook_override")
    @classmethod
    def validate_webhook_override(cls, v: str):
        return MsTeamsWebhookUrlTransformer.validate_webhook_override(v)


class MsTeamsSinkConfigWrapper(SinkConfigBase):
    ms_teams_sink: MsTeamsSinkParams

    def get_params(self) -> SinkBaseParams:
        return self.ms_teams_sink
