import json

from typing import List

from ....model.data_types import ServiceInfo
from ....reporting.blocks import Finding
from .dal.supabase_dal import SupabaseDal
from ..sink_base import SinkBase
from pydantic import BaseModel
import threading
from collections import defaultdict


class RobustaSinkConfig(BaseModel):
    store_url: str
    api_key: str
    account_id: str


class RobustaSink(SinkBase):
    def __init__(
        self, sink_config: RobustaSinkConfig, sink_name: str, cluster_name: str
    ):
        super().__init__(sink_name)
        self.dal = SupabaseDal(
            sink_config.store_url,
            sink_config.api_key,
            sink_config.account_id,
            sink_name,
            cluster_name,
        )

    def write_finding(self, finding: Finding):
        self.dal.persist_finding(finding)

    def write_service(self, service: ServiceInfo):
        self.dal.persist_service(service)

    def get_active_services(self) -> List[ServiceInfo]:
        return self.dal.get_active_services()


class RobustaSinkManager:

    manager_lock = threading.Lock()
    sink_map = defaultdict(None)

    @staticmethod
    def get_robusta_sink(
        sink_name: str, sink_config: RobustaSinkConfig, cluster_name: str
    ) -> SinkBase:
        with RobustaSinkManager.manager_lock:
            sink_key = (
                sink_config.account_id + sink_config.store_url + sink_config.api_key
            )
            sink = RobustaSinkManager.sink_map.get(sink_key)
            if sink is not None:
                return sink
            sink = RobustaSink(sink_config, sink_name, cluster_name)
            RobustaSinkManager.sink_map[sink_key] = sink
            return sink
