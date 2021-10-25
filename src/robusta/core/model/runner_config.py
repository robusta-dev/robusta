from typing import List, Optional, Union

from pydantic import BaseModel

from ...model.playbook_definition import PlaybookDefinition
from ..sinks.datadog.datadog_sink import DataDogSinkConfigWrapper
from ..sinks.kafka.kafka_sink import KafkaSinkConfigWrapper
from ..sinks.robusta.robusta_sink import RobustaSinkConfigWrapper
from ..sinks.slack.slack_sink import SlackSinkConfigWrapper


class RunnerConfig(BaseModel):
    playbook_sets: List[str] = ["defaults", "custom"]
    sinks_config: Optional[
        List[
            Union[
                RobustaSinkConfigWrapper,
                SlackSinkConfigWrapper,
                DataDogSinkConfigWrapper,
                KafkaSinkConfigWrapper,
            ]
        ]
    ]
    global_config: Optional[dict] = {}
    active_playbooks: Optional[List[PlaybookDefinition]] = []
