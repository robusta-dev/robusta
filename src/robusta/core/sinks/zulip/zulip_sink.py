import certifi
import requests

from robusta.core.model.env_vars import ADDITIONAL_CERTIFICATE
from robusta.core.reporting.base import Finding
from robusta.core.sinks.sink_base import SinkBase
from robusta.core.sinks.zulip.zulip_sink_params import ZulipSinkConfigWrapper
from robusta.integrations import zulip as zulip_module

ZULIP_MESSAGE_DEFAULT_LEN: int = 10_000


class ZulipSink(SinkBase):
    def __init__(self, sink_config: ZulipSinkConfigWrapper, registry):
        super().__init__(sink_config.zulip_sink, registry)
        self.bot_email = sink_config.zulip_sink.bot_email
        self.bot_api_key = sink_config.zulip_sink.bot_api_key
        self.api_url = sink_config.zulip_sink.api_url

        self.zclient = requests.Session()
        self.zclient.auth = (self.bot_email, self.bot_api_key.get_secret_value())
        if ADDITIONAL_CERTIFICATE:
            self.zclient.verify = certifi.where()
        else:
            self.zclient.verify = False

        self.zulip_sender = zulip_module.ZulipSender(
            self.api_url, self.zclient, self.account_id, self.cluster_name, self.signing_key
        )

    def write_finding(self, finding: Finding, platform_enabled: bool):
        self.zulip_sender.send_finding_to_zulip(finding, self.params, platform_enabled)
