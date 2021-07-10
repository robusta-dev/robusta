from typing import List, Optional

from pydantic import BaseModel

from .playbook_deploy_config import PlaybookDeployConfig


class RunnerConfig(BaseModel):
    global_config: Optional[dict] = {}
    active_playbooks: Optional[List[PlaybookDeployConfig]] = []
