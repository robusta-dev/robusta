from robusta.core.reporting.base import Finding
from robusta.core.sinks.sink_base import SinkBase
from robusta.core.sinks.mail.mail_sink_params import MailSinkConfigWrapper
from robusta.integrations.mail.sender import MailSender


class MailSink(SinkBase):
    def __init__(self, sink_config: MailSinkConfigWrapper, registry):
        super().__init__(sink_config.mail_sink, registry)
        self.sender = MailSender(
            sink_config.mail_sink.mailto,
            self.signing_key,
            self.account_id,
            self.cluster_name,
        )

    def write_finding(self, finding: Finding, platform_enabled: bool):
        self.sender.send_finding(finding, platform_enabled, self.params.with_header)
