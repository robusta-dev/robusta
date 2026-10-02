from typing import List

from robusta.core.reporting.base import Finding
from robusta.core.sinks.plivo.plivo_client import PlivoClient
from robusta.core.sinks.plivo.plivo_sink_params import PlivoSinkConfigWrapper
from robusta.core.sinks.sink_base import SinkBase

MAX_SMS_LENGTH = 1600


class PlivoSink(SinkBase):
    def __init__(self, sink_config: PlivoSinkConfigWrapper, registry):
        super().__init__(sink_config.plivo_sink, registry)

        self.client = PlivoClient(
            sink_config.plivo_sink.auth_id,
            sink_config.plivo_sink.auth_token.get_secret_value(),
        )
        self.from_number = sink_config.plivo_sink.from_number
        self.to_number = sink_config.plivo_sink.to_number

    def write_finding(self, finding: Finding, platform_enabled: bool):
        message = self.__build_message(finding, platform_enabled)
        self.client.send_message(src=self.from_number, dst=self.to_number, text=message)

    def __build_message(self, finding: Finding, platform_enabled: bool) -> str:
        lines: List[str] = [f"{finding.severity.name} - {finding.title}"]

        if platform_enabled:
            lines.append(f"Investigate: {finding.get_investigate_uri(self.account_id, self.cluster_name)}")

        lines.append(f"Source: {self.cluster_name}")

        if finding.description:
            lines.append(finding.description)

        message = "\n".join(line for line in lines if line)
        return message[:MAX_SMS_LENGTH]
