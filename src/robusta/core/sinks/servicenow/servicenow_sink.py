from robusta.core.reporting.base import Finding
from robusta.core.sinks.servicenow.servicenow_sink_params import ServiceNowSinkConfigWrapper
from robusta.core.sinks.sink_base import SinkBase
from robusta.integrations.servicenow.sender import ServiceNowSender


class ServiceNowSink(SinkBase):
    def __init__(self, sink_config: ServiceNowSinkConfigWrapper, registry):
        super().__init__(sink_config.service_now_sink, registry)
        self.sender = ServiceNowSender(
            self.params, account_id=self.account_id, cluster_name=self.cluster_name, signing_key=self.signing_key
        )

    def write_finding(self, finding: Finding, platform_enabled: bool):
        self.sender.send_finding(finding, platform_enabled)
