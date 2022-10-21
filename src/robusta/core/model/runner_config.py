from typing import List, Optional, Union, Dict
from pydantic import BaseModel, SecretStr, validator

from ..playbooks.playbook_utils import get_env_replacement, replace_env_vars_values
from ..sinks.webhook.webhook_sink_params import WebhookSinkConfigWrapper
from ..sinks.telegram.telegram_sink_params import TelegramSinkConfigWrapper
from ...model.playbook_definition import PlaybookDefinition
from ..sinks.datadog.datadog_sink_params import DataDogSinkConfigWrapper
from ..sinks.kafka.kafka_sink_params import KafkaSinkConfigWrapper
from ..sinks.msteams.msteams_sink_params import MsTeamsSinkConfigWrapper
from ..sinks.robusta.robusta_sink_params import RobustaSinkConfigWrapper
from ..sinks.slack.slack_sink_params import SlackSinkConfigWrapper
from ..sinks.opsgenie.opsgenie_sink_params import OpsGenieSinkConfigWrapper
from ..sinks.victorops.victorops_sink_params import VictoropsConfigWrapper
from ..sinks.pagerduty.pagerduty_sink_params import PagerdutyConfigWrapper
from ..sinks.discord.discord_sink_params import DiscordSinkConfigWrapper
from ..sinks.mattermost.mattermost_sink_params import MattermostSinkConfigWrapper
from ..sinks.webex.webex_sink_params import WebexSinkConfigWrapper

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
                OpsGenieSinkConfigWrapper,
                TelegramSinkConfigWrapper,
                WebhookSinkConfigWrapper,
                VictoropsConfigWrapper,
                PagerdutyConfigWrapper,
                DiscordSinkConfigWrapper,
                MattermostSinkConfigWrapper,
                WebexSinkConfigWrapper
            ]
        ]
    ]
    global_config: Optional[dict] = {}
    active_playbooks: Optional[List[PlaybookDefinition]] = []

    @validator('playbook_repos')
    def env_var_repo_keys(cls, playbook_repos: Dict[str, PlaybookRepo]):
        return {k: RunnerConfig._replace_env_var_in_playbook_repo(v) for k, v in playbook_repos.items()}

    @staticmethod
    def _replace_env_var_in_playbook_repo(playbook_repo: PlaybookRepo):
        if not playbook_repo.key:
            return playbook_repo
        env_var_replacement = get_env_replacement(playbook_repo.key.get_secret_value())
        if env_var_replacement:
            playbook_repo.key = SecretStr(env_var_replacement)

        return playbook_repo

    @validator('global_config')
    def env_var_params(cls, global_config: dict):
        return replace_env_vars_values(global_config)
