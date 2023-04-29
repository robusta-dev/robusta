from typing import Optional, List
from pydantic import BaseModel
from base64 import b64decode
from datetime import datetime
import gzip
import json


class Metadata(BaseModel):
    name: str
    version: str
    description: str
    apiVersion: str
    appVersion: str


class Chart(BaseModel):
    metadata: Metadata


class Info(BaseModel):
    first_deployed: datetime
    last_deployed: datetime
    deleted: str
    description: str
    status: str
    notes: str


class HelmRelease(BaseModel):
    name: str
    info: Info
    chart: Optional[Chart]
    version: int
    namespace: str

    @classmethod
    def from_json(cls, release_data: dict) -> "HelmRelease":
        return cls(
            name=release_data.get("name", None),
            info=release_data.get("info", None),
            chart=release_data.get("chart", None),
            version=release_data.get("version", None),
            namespace=release_data.get("namespace", None),
        )

    def to_dict(self):
        data = json.loads(self.json())
        data['info']['first_deployed'] = self.info.first_deployed.isoformat()
        data['info']['last_deployed'] = self.info.last_deployed.isoformat()
        return data

    @staticmethod
    def list_to_json(releases: List["HelmRelease"]):
        return [release.to_dict() for release in releases]

    @classmethod
    def from_api_server(cls, encoded_release_data: str) -> "HelmRelease":
        # k8 base64 dec
        release_data = b64decode(encoded_release_data)

        # helm base64 dec
        release_data = b64decode(release_data)

        # un-gzip
        decompressed_data = gzip.decompress(release_data)
        decompressed_data = decompressed_data.decode('utf-8')

        return cls.from_json(json.loads(decompressed_data))

    @classmethod
    def from_db_row(cls, data: dict) -> "HelmRelease":
        return HelmRelease(
            name=data["name"],
            info=Info(**data.get("info", {})),
            chart=Chart(**data.get("chart", {})),
            version=data["version"],
            namespace=data["namespace"],

        )

    def get_service_key(self) -> str:
        return f"{self.namespace}/{self.name}"
