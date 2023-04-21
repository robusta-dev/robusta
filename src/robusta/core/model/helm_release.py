from typing import Optional
from pydantic import BaseModel
from base64 import b64decode
import gzip
import json


class HelmRelease(BaseModel):
    name: str
    info: Optional[dict]
    chart: Optional[dict]
    config: Optional[dict]
    manifest: Optional[str]
    version: int
    namespace: str

    @classmethod
    def from_json(cls, release_data: dict) -> "HelmRelease":
        return cls(
            name=release_data.get("name", None),
            info=release_data.get("info", {}),
            chart=release_data.get("chart", {}),
            config=release_data.get("config", {}),
            manifest=release_data.get("manifest", None),
            version=release_data.get("version", None),
            namespace=release_data.get("namespace", None),
        )

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
    def from_db_row(cls, release_data: dict) -> "HelmRelease":
        return cls(
            name=release_data["name"],
            info=release_data["info"],
            chart=release_data["chart"],
            config=release_data["config"],
            manifest=release_data["manifest"],
            version=release_data["version"],
            namespace=release_data["namespace"],
        )
