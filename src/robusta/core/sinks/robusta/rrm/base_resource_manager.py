from typing import Optional, List

from robusta.core.sinks.robusta.rrm.types import ResourceKind, AccountResource


class BaseResourceHandler:
    def __init__(self, resource_kind: ResourceKind, cluster: str):
        self.__latest_revision = None
        self._resource_kind = resource_kind
        self.cluster = cluster

    def handle_resources(self, resources: List[AccountResource]) -> Optional[str]:
        pass
