import re
from typing import Optional
from urllib.parse import urlparse
from robusta.core.playbooks.playbook_utils import get_env_replacement

from pydantic import validator

from robusta.core.sinks.sink_base_params import SinkBaseParams
from robusta.core.sinks.sink_config import SinkConfigBase

class IncidentioSinkParams(SinkBaseParams):
    base_url: Optional[str] = "https://api.incident.io/v2/"
    token: str
    source_config_id: str

    @classmethod
    def _get_sink_type(cls):
        return "incidentio"
    
    @validator("base_url")
    def validate_base_url(cls, base_url):
        parsed_url = urlparse(base_url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError(f"Invalid base_url: {base_url}. It must include a scheme and netloc (e.g., https://api.incident.io).")
        return base_url

    @validator("source_config_id")
    def validate_source_config_id(cls, source_config_id):
        """
        Ensures source_config_id matches the expected format.
        """
        pattern = r"^[A-Z0-9]{26}$"
        source_config_id = get_env_replacement(source_config_id)
        if not re.match(pattern, source_config_id):
            raise ValueError(
                f"Invalid source_config_id: {source_config_id}. It must be a 26-character string of uppercase letters and digits."
            )
        return source_config_id

class IncidentioSinkConfigWrapper(SinkConfigBase):
    incidentio_sink: IncidentioSinkParams

    def get_params(self) -> SinkBaseParams:
        return self.incidentio_sink