import logging
from typing import Optional
import requests
from pydantic import BaseModel, ConfigDict

from robusta.core.model.env_vars import ROBUSTA_API_ENDPOINT

RUNNER_GET_INFO_URL = f"{ROBUSTA_API_ENDPOINT}/api/runner/get_info"
TIMEOUT = 2


class RunnerInfo(BaseModel):
    model_config = ConfigDict(extra="ignore")
    latest_version: Optional[str] = None


def fetch_runner_info() -> Optional[RunnerInfo]:
    try:
        response = requests.get(RUNNER_GET_INFO_URL, timeout=TIMEOUT)
        response.raise_for_status()
        result = response.json()
        return RunnerInfo(**result)
    except Exception:
        logging.info("Failed to fetch runner info")
        return None
