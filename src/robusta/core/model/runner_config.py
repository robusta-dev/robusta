from typing import List, Optional, Union, Dict
from pydantic import BaseModel, SecretStr

from ...model.playbook_definition import PlaybookDefinition
from ..sinks.datadog.datadog_sink import DataDogSinkConfigWrapper
from ..sinks.kafka.kafka_sink import KafkaSinkConfigWrapper
from ..sinks.robusta.robusta_sink import RobustaSinkConfigWrapper
from ..sinks.slack.slack_sink import SlackSinkConfigWrapper
from ..sinks.msteams.msteams_sink import MsTeamsSinkConfigWrapper


class PlaybookRepo(BaseModel):
    url: str
    key: Optional[SecretStr] = SecretStr("")
    pip_install: bool = (
        True  # Set to False, if the playbooks package is already in site-packages.
    )


class RunnerConfig(BaseModel):
    playbook_repos: Dict[str, PlaybookRepo]
    sinks_config: Optional[
        List[
            Union[
                RobustaSinkConfigWrapper,
                SlackSinkConfigWrapper,
                DataDogSinkConfigWrapper,
                KafkaSinkConfigWrapper,
                MsTeamsSinkConfigWrapper,
            ]
        ]
    ]
    global_config: Optional[dict] = {}
    active_playbooks: Optional[List[PlaybookDefinition]] = []
