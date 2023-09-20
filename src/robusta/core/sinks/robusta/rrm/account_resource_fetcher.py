from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

from robusta.core.sinks.robusta.rrm.types import AccountResource, ResourceKind, AccountResourceStatusType, \
    AccountResourceStatusInfo


class AccountResourceFetcher(ABC):
    @abstractmethod
    def get_account_resources(
            self, resource_kind: ResourceKind, updated_at: Optional[datetime]
    ) -> List[AccountResource]:
        pass

    @abstractmethod
    def set_account_resource_status(
            self, status_type: Optional[AccountResourceStatusType],
            info: Optional[AccountResourceStatusInfo]
    ):
        pass
