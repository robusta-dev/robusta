from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

from robusta.core.model.cluster_status import Account
from robusta.core.sinks.robusta.rrm.types import AccountResource, ResourceKind


class AccountResourceFetcher(ABC):
    @abstractmethod
    def get_account_resources(
        self, resource_kind: ResourceKind, updated_at: Optional[datetime]
    ) -> List[AccountResource]:
        pass

    @abstractmethod
    def get_account(self, account_id: str) -> Optional[Account]:
        pass
