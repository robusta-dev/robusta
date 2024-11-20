from typing import Dict, List, Optional

from robusta.core.sinks.sink_base_params import SinkBaseParams
from robusta.core.sinks.sink_config import SinkConfigBase


class JiraSinkParams(SinkBaseParams):
    url: str
    username: str
    api_key: str
    issue_type: str = "Task"
    dedups: List[str] = ["fingerprint"]
    project_name: str
    project_type_id_override: Optional[int]
    issue_type_id_override: Optional[int]
    sendResolved: Optional[bool]
    reopenIssues: Optional[bool]
    doneStatusName: Optional[str] = "Done"
    reopenStatusName: Optional[str] = "To Do"
    noReopenResolution: Optional[str] = ""
    epic: Optional[str] = ""
    assignee: Optional[str] = ""
    priority_mapping: Optional[Dict[str, str]] = None


    @classmethod
    def _get_sink_type(cls):
        return "jira"


class JiraSinkConfigWrapper(SinkConfigBase):
    jira_sink: JiraSinkParams

    def get_params(self) -> SinkBaseParams:
        return self.jira_sink
