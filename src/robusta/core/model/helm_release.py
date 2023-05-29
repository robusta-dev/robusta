from typing import Optional, List, Any, Dict
from pydantic import BaseModel
from base64 import b64decode
from datetime import datetime
import gzip
import json


class Metadata(BaseModel):
    name: str
    version: str
    description: Optional[str]
    apiVersion: Optional[str]
    appVersion: Optional[str]


class Chart(BaseModel):
    metadata: Metadata


class Info(BaseModel):
    first_deployed: datetime
    last_deployed: datetime
    deleted: str
    description: Optional[str]
    status: str
    notes: Optional[str]


class HelmRelease(BaseModel):
    name: str
    info: Info
    chart: Optional[Chart]
    version: int
    namespace: str
    deleted: bool = False

    @staticmethod
    def list_to_dict(releases: List["HelmRelease"]):
        return [release.dict() for release in releases]

    def dict(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        release_dict = super().dict()
        release_dict["info"]["first_deployed"] = self.info.first_deployed.isoformat()
        release_dict["info"]["last_deployed"] = self.info.last_deployed.isoformat()
        return release_dict

    @classmethod
    def from_api_server(cls, encoded_release_data: str) -> "HelmRelease":
        # k8 base64 dec
        release_data = b64decode(encoded_release_data)

        # helm base64 dec
        release_data = b64decode(release_data)

        # un-gzip
        decompressed_data = gzip.decompress(release_data)
        decompressed_data = decompressed_data.decode('utf-8')

        return HelmRelease(**json.loads(decompressed_data))

    @classmethod
    def from_db_row(cls, data: dict) -> "HelmRelease":
        return HelmRelease(**data)

    def get_service_key(self) -> str:
        return f"{self.namespace}/HelmRelease/{self.name}"
