from typing import Optional, List

from hikaru.model.rel_1_26 import OwnerReference
from pydantic import BaseModel


class FindingOwner(BaseModel):
    owner_references: Optional[List[OwnerReference]] = None
    unknown_owner: bool = False
