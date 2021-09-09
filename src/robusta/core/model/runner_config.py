from typing import List, Optional

from pydantic import BaseModel

from .playbook_deploy_config import PlaybookDeployConfig
from ..sinks.sink_config import SinkConfigBase


class RunnerConfig(BaseModel):
    playbook_sets: List[str] = ["defaults", "custom"]
    sinks_config: Optional[List[SinkConfigBase]] = []
    global_config: Optional[dict] = {}
    active_playbooks: Optional[List[PlaybookDeployConfig]] = []
