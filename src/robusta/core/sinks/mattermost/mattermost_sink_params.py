from pydantic import validator
from urllib.parse import urlparse

from ..sink_base_params import SinkBaseParams
from ..sink_config import SinkConfigBase


class MattermostSinkParams(SinkBaseParams):
    url: str
    token: str
    token_id: str
    channel: str

    @validator("url")
    def set_http_schema(cls, url):
        parsed_url = urlparse(url)
        # if netloc is empty string, the url was provided without schema
        if not parsed_url.netloc:
            raise AttributeError(f"{url} does not contain the schema!")
        return url


class MattermostSinkConfigWrapper(SinkConfigBase):
    mattermost_sink: MattermostSinkParams

    def get_params(self) -> SinkBaseParams:
        return self.mattermost_sink
