from datetime import datetime
from typing import Optional, List

from robusta.core.sinks.robusta.rrm.account_resource_fetcher import AccountResourceFetcher
from robusta.core.sinks.robusta.rrm.types import ResourceKind, AccountResourceStatusType, AccountResource, \
    AccountResourceStatusInfo


class BaseResourceManager:
    def __init__(self, resource_kind: ResourceKind, cluster: str, dal: AccountResourceFetcher, ):
        self.__last_updated_at = None
        self._resource_kind = resource_kind
        self.cluster = cluster
        self.dal = dal

    def init_resources(self, updated_at: Optional[datetime]):
        pass

    def get_resource_kind(self) -> ResourceKind:
        return self._resource_kind

    def set_last_updated_at(self, updated_at: Optional[datetime]):
        self.__last_updated_at = updated_at

    def set_account_resource_status(
            self, status_type: Optional[AccountResourceStatusType],
            info: Optional[AccountResourceStatusInfo]
    ):
        self.dal.set_account_resource_status(status_type=status_type, info=info)

    def get_last_updated_at(self) -> Optional[datetime]:
        return self.__last_updated_at

    def prepare(self, account_resources: List[AccountResource]):
        """Initialize resources"""

        pass
