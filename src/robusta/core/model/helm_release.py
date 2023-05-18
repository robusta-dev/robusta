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
    first_deployed: str
    last_deployed: str
    deleted: str
    description: str
    status: str
    notes: Optional[str]

    def get_last_deployed(self):
        return datetime.strptime(self.last_deployed, '%Y-%m-%dT%H:%M:%S.%f%z')

    def get_first_deployed(self):
        return datetime.strptime(self.first_deployed, '%Y-%m-%dT%H:%M:%S.%f%z')


class HelmRelease(BaseModel):
    name: str
    info: Info
    chart: Chart
    version: int
    namespace: str
    deleted: bool = False

    @staticmethod
    def list_to_json(releases: List["HelmRelease"]):
        return [release.dict() for release in releases]

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
