from .sink_base_params import SinkBaseParams
from ...core.reporting.base import Finding


class SinkBase:
    def __init__(self, sink_params: SinkBaseParams, registry):
        self.sink_name = sink_params.name
        self.params = sink_params
        self.default = sink_params.default
        self.registry = registry
        global_config = self.registry.get_global_config()

        self.account_id = global_config.get("account_id", "")
        self.cluster_name = global_config.get("cluster_name", "")
        self.signing_key = global_config.get("signing_key", "")

    def is_global_config_changed(self):
        # registry global config can be updated without these stored values being changed
        global_config = self.registry.get_global_config()
        account_id = global_config.get("account_id", "")
        cluster_name = global_config.get("cluster_name", "")
        signing_key = global_config.get("signing_key", "")
        return (self.account_id != account_id
                    or self.cluster_name != cluster_name
                    or self.signing_key != signing_key)

    def stop(self):
        pass

    def accepts(self, finding: Finding) -> bool:
        return finding.matches(self.params.match)

    def write_finding(self, finding: Finding, platform_enabled: bool):
        raise NotImplementedError(
            f"write_finding not implemented for sink {self.sink_name}"
        )
