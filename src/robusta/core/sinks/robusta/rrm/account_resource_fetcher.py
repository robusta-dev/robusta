from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Dict

from robusta.core.sinks.robusta.rrm.types import AccountResource, ResourceKind, AccountResourceStatusType, \
    AccountResourceStatusInfo


class AccountResourceFetcher(ABC):
    @abstractmethod
    def get_account_resources(
            self, resource_kind: Optional[ResourceKind] = None, latest_revision: Optional[datetime] = None,
    ) -> Dict[ResourceKind, List[AccountResource]]:
        pass

    @abstractmethod
    def set_account_resource_status(
            self, status_type: AccountResourceStatusType,
            info: Optional[AccountResourceStatusInfo],
            latest_revision: datetime
    ):
        pass
