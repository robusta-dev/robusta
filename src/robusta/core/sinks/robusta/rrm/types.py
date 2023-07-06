from datetime import datetime
from enum import Enum
from typing import List, Optional, Union
from pydantic import BaseModel


class ResourceKind(str, Enum):
    PrometheusAlert = "PrometheusAlert"


class AccountResource(BaseModel):
    entity_id: str
    resource_kind: ResourceKind
    clusters_target_set: Optional[List[str]] = None
    resource_state: Optional[dict] = None
    deleted: bool = False
    updated_at: datetime


class ResourceEntry(BaseModel):
    resource: AccountResource


class BaseResourceManager:
    def __init__(self, resource_kind: ResourceKind) -> None:
        self._timestamp = None
        self._resource_kind = resource_kind

    # get the latest timestamp to use
    def get_updated_ts(self) -> datetime:
        return self._timestamp

    # get resource kind
    def get_resource_kind(self) -> ResourceKind:
        return self._resource_kind

    # create resources
    def create_resource(self, resource: AccountResource) -> Union[ResourceEntry, None]:
        pass

    # update resources
    def update_resource(self, resource: AccountResource, old_entry: ResourceEntry) -> Union[ResourceEntry, None]:
        pass

    # delete resources
    def delete_resource(self, resource: AccountResource, old_entry: ResourceEntry) -> True:
        pass

    # initialize resources
    def init_resources(self) -> bool:
        pass
