from typing import List, Optional, Union, Dict
from pydantic import BaseModel, SecretStr

from ...model.playbook_definition import PlaybookDefinition
from ..sinks.datadog.datadog_sink_params import DataDogSinkConfigWrapper
from ..sinks.kafka.kafka_sink_params import KafkaSinkConfigWrapper
from ..sinks.msteams.msteams_sink_params import MsTeamsSinkConfigWrapper
from ..sinks.robusta.robusta_sink_params import RobustaSinkConfigWrapper
from ..sinks.slack.slack_sink_params import SlackSinkConfigWrapper


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
