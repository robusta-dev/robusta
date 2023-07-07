from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

from core.sinks.robusta.rrm.types import AccountResource, ResourceKind


class AccountingResourceFetcher(ABC):
    @abstractmethod
    def get_account_resources(
        self, resource_kind: ResourceKind, updated_at: Optional[datetime]
    ) -> List[AccountResource]:
        pass
