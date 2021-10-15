from typing import List, Optional, Union

from pydantic import BaseModel

from ...model.playbook_definition import PlaybookDefinition
from ..sinks.datadog.datadog_sink import DataDogSinkConfig
from ..sinks.kafka.kafka_sink import KafkaSinkConfig
from ..sinks.robusta.robusta_sink import RobustaSinkConfig
from ..sinks.slack.slack_sink import SlackSinkConfig


class RunnerConfig(BaseModel):
    playbook_sets: List[str] = ["defaults", "custom"]
    sinks_config: Optional[
        List[
            Union[
                RobustaSinkConfig,
                SlackSinkConfig,
                DataDogSinkConfig,
                KafkaSinkConfig,
            ]
        ]
    ]
    global_config: Optional[dict] = {}
    active_playbooks: Optional[List[PlaybookDefinition]] = []
