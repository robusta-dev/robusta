from robusta.core.reporting.base import Finding
from robusta.core.sinks.sink_base import SinkBase
from robusta.core.sinks.mail.mail_sink_params import MailSinkConfigWrapper
from robusta.integrations.mail.sender import MailSender


class MailSink(SinkBase):
    def __init__(self, sink_config: MailSinkConfigWrapper, registry):
        super().__init__(sink_config.mail_sink, registry)
        params = sink_config.mail_sink

        self.sender = MailSender(
            params.mailto,
            self.signing_key,
            self.account_id,
            self.cluster_name,
            use_ses=params.use_ses,
            aws_region=params.aws_region,
            from_email=params.from_email,
            aws_access_key_id=params.aws_access_key_id,
            aws_secret_access_key=params.aws_secret_access_key,
            configuration_set=params.configuration_set,
            skip_ses_init=params.skip_ses_init,
        )

    def write_finding(self, finding: Finding, platform_enabled: bool):
        self.sender.send_finding(finding, platform_enabled, self.params.with_header)
