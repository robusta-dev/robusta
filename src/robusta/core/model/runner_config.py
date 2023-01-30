from typing import Dict, List, Optional, Union

from pydantic import BaseModel, SecretStr, validator

from robusta.core.playbooks.playbook_utils import get_env_replacement, replace_env_vars_values
from robusta.core.sinks.datadog.datadog_sink_params import DataDogSinkConfigWrapper
from robusta.core.sinks.discord.discord_sink_params import DiscordSinkConfigWrapper
from robusta.core.sinks.jira.jira_sink_params import JiraSinkConfigWrapper
from robusta.core.sinks.kafka.kafka_sink_params import KafkaSinkConfigWrapper
from robusta.core.sinks.mattermost.mattermost_sink_params import MattermostSinkConfigWrapper
from robusta.core.sinks.msteams.msteams_sink_params import MsTeamsSinkConfigWrapper
from robusta.core.sinks.opsgenie.opsgenie_sink_params import OpsGenieSinkConfigWrapper
from robusta.core.sinks.pagerduty.pagerduty_sink_params import PagerdutyConfigWrapper
from robusta.core.sinks.robusta.robusta_sink_params import RobustaSinkConfigWrapper
from robusta.core.sinks.slack.slack_sink_params import SlackSinkConfigWrapper
from robusta.core.sinks.telegram.telegram_sink_params import TelegramSinkConfigWrapper
from robusta.core.sinks.victorops.victorops_sink_params import VictoropsConfigWrapper
from robusta.core.sinks.webex.webex_sink_params import WebexSinkConfigWrapper
from robusta.core.sinks.webhook.webhook_sink_params import WebhookSinkConfigWrapper
from robusta.model.playbook_definition import PlaybookDefinition


class PlaybookRepo(BaseModel):
    url: str
    key: Optional[SecretStr] = SecretStr("")
    pip_install: bool = True  # Set to False, if the playbooks package is already in site-packages.


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
                WebexSinkConfigWrapper,
                JiraSinkConfigWrapper,
            ]
        ]
    ]
    light_actions: Optional[List[str]]
    global_config: Optional[dict] = {}
    active_playbooks: Optional[List[PlaybookDefinition]] = []

    @validator("playbook_repos")
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

    @validator("global_config")
    def env_var_params(cls, global_config: dict):
        return replace_env_vars_values(global_config)
