import base64
import logging
from typing import Dict, List, Optional, Union, cast

from pydantic.v1 import BaseModel, SecretStr, root_validator, validator

from robusta.core.playbooks.playbook_utils import get_env_replacement, replace_env_vars_values
from robusta.core.sinks.datadog.datadog_sink_params import DataDogSinkConfigWrapper
from robusta.core.sinks.discord.discord_sink_params import DiscordSinkConfigWrapper
from robusta.core.sinks.file.file_sink_params import FileSinkConfigWrapper
from robusta.core.sinks.google_chat.google_chat_params import GoogleChatSinkConfigWrapper
from robusta.core.sinks.jira.jira_sink_params import JiraSinkConfigWrapper
from robusta.core.sinks.kafka.kafka_sink_params import KafkaSinkConfigWrapper
from robusta.core.sinks.mattermost.mattermost_sink_params import MattermostSinkConfigWrapper
from robusta.core.sinks.msteams.msteams_sink_params import MsTeamsSinkConfigWrapper
from robusta.core.sinks.msteams_graph.msteams_graph_sink_params import MsTeamsGraphSinkConfigWrapper
from robusta.core.sinks.opsgenie.opsgenie_sink_params import OpsGenieSinkConfigWrapper
from robusta.core.sinks.pagerduty.pagerduty_sink_params import PagerdutyConfigWrapper
from robusta.core.sinks.robusta.robusta_sink_params import RobustaSinkConfigWrapper
from robusta.core.sinks.rocketchat.rocketchat_sink_params import RocketchatSinkConfigWrapper
from robusta.core.sinks.servicenow.servicenow_sink_params import ServiceNowSinkConfigWrapper
from robusta.core.sinks.slack.slack_sink_params import SlackSinkConfigWrapper
from robusta.core.sinks.slack.preview.slack_sink_preview_params import SlackSinkPreviewConfigWrapper
from robusta.core.sinks.mail.mail_sink_params import MailSinkConfigWrapper
from robusta.core.sinks.telegram.telegram_sink_params import TelegramSinkConfigWrapper
from robusta.core.sinks.victorops.victorops_sink_params import VictoropsConfigWrapper
from robusta.core.sinks.webex.webex_sink_params import WebexSinkConfigWrapper
from robusta.core.sinks.webhook.webhook_sink_params import WebhookSinkConfigWrapper
from robusta.core.sinks.yamessenger.yamessenger_sink_params import YaMessengerSinkConfigWrapper
from robusta.core.sinks.pushover.pushover_sink_params import PushoverSinkConfigWrapper
from robusta.core.sinks.zulip.zulip_sink_params import ZulipSinkConfigWrapper
from robusta.model.alert_relabel_config import AlertRelabel
from robusta.model.playbook_definition import PlaybookDefinition
from robusta.utils.base64_utils import is_base64_encoded
from robusta.core.sinks.sink_config import SinkConfigBase
from robusta.core.sinks.incidentio.incidentio_sink_params import IncidentioSinkConfigWrapper


REMOVED_HELM_RELEASE_TRIGGERS = {"on_helm_release_unhealthy", "on_helm_release_fail", "on_helm_release_deploy"}
REMOVED_HELM_RELEASE_ACTIONS = {"helm_status_enricher"}


def _has_removed_key(entry, removed: set) -> bool:
    return isinstance(entry, dict) and bool(removed & entry.keys())


class PlaybookRepo(BaseModel):
    url: str
    key: Optional[SecretStr] = SecretStr("")
    branch: Optional[str] = None  # when url is a git repo
    pip_install: bool = True  # Set to False, if the playbooks package is already in site-packages.
    http_headers: Optional[Dict[str, str]] = None
    build_isolation: bool = False

    @root_validator
    def validate_pip_build_isolation(cls, values: Dict) -> Dict:
        if values.get("build_isolation") and not values.get("pip_install"):
            raise ValueError("build_isolation should not be specified for non-pip builds")
        return values


class RunnerConfig(BaseModel):
    playbook_repos: Dict[str, PlaybookRepo]
    sinks_config: Optional[
        List[
            Union[
                RobustaSinkConfigWrapper,
                SlackSinkConfigWrapper,
                SlackSinkPreviewConfigWrapper,
                DataDogSinkConfigWrapper,
                KafkaSinkConfigWrapper,
                MsTeamsSinkConfigWrapper,
                MsTeamsGraphSinkConfigWrapper,
                RocketchatSinkConfigWrapper,
                OpsGenieSinkConfigWrapper,
                TelegramSinkConfigWrapper,
                WebhookSinkConfigWrapper,
                VictoropsConfigWrapper,
                PagerdutyConfigWrapper,
                DiscordSinkConfigWrapper,
                MattermostSinkConfigWrapper,
                WebexSinkConfigWrapper,
                YaMessengerSinkConfigWrapper,
                JiraSinkConfigWrapper,
                FileSinkConfigWrapper,
                MailSinkConfigWrapper,
                PushoverSinkConfigWrapper,
                GoogleChatSinkConfigWrapper,
                ServiceNowSinkConfigWrapper,
                ZulipSinkConfigWrapper,
                IncidentioSinkConfigWrapper
            ]
        ]
    ]
    light_actions: Optional[List[str]]
    command_actions: Optional[List[str]] = []
    global_config: Optional[dict] = {}
    active_playbooks: Optional[List[PlaybookDefinition]] = []
    alert_relabel: Optional[List[AlertRelabel]] = []

    @validator("active_playbooks", pre=True)
    def drop_helm_release_playbooks(cls, playbooks):
        if not isinstance(playbooks, list):
            return playbooks
        kept = []
        for playbook in playbooks:
            triggers = playbook.get("triggers") if isinstance(playbook, dict) else None
            actions = playbook.get("actions") if isinstance(playbook, dict) else None
            if not isinstance(triggers, list) or not isinstance(actions, list):
                kept.append(playbook)
                continue
            other_triggers = [t for t in triggers if not _has_removed_key(t, REMOVED_HELM_RELEASE_TRIGGERS)]
            other_actions = [a for a in actions if not _has_removed_key(a, REMOVED_HELM_RELEASE_ACTIONS)]
            if len(other_triggers) == len(triggers) and len(other_actions) == len(actions):
                kept.append(playbook)
                continue
            removed = sorted(
                key
                for entry in triggers + actions
                if isinstance(entry, dict)
                for key in entry.keys() & (REMOVED_HELM_RELEASE_TRIGGERS | REMOVED_HELM_RELEASE_ACTIONS)
            )
            if other_triggers and other_actions:
                kept.append({**playbook, "triggers": other_triggers, "actions": other_actions})
                outcome = f"Removed {removed} from the playbook"
            else:
                outcome = f"Skipping the playbook that uses {removed}"
            name = f" {playbook['name']}" if playbook.get("name") else ""
            logging.error(
                f"{outcome}{name}: Helm releases monitoring is no longer supported, remove it from your playbooks"
            )
        return kept

    @root_validator()
    def ensure_unique_sink_name(cls, val: Dict) -> Dict:
        if val.get('sinks_config'):
            value_set = set()
            sinksConfig = cast(List[SinkConfigBase], val.get('sinks_config'))
            for sink_config in sinksConfig:
                sink_name = sink_config.get_name()
                if sink_name in value_set:
                    raise ValueError(f"Sink name \"{sink_name}\" is already defined. Sink names must be unique.")

                value_set.add(sink_name)
        return val

    @validator("playbook_repos")
    def env_var_repo_keys(cls, playbook_repos: Dict[str, PlaybookRepo]):
        return {k: RunnerConfig._replace_env_var_in_playbook_repo(v) for k, v in playbook_repos.items()}

    @staticmethod
    def _replace_env_var_in_playbook_repo(playbook_repo: PlaybookRepo):
        url_env_var_replacement = get_env_replacement(playbook_repo.url)
        if url_env_var_replacement:
            playbook_repo.url = url_env_var_replacement

        if not playbook_repo.key:
            return playbook_repo

        env_var_replacement = get_env_replacement(playbook_repo.key.get_secret_value())
        if env_var_replacement:
            playbook_repo.key = SecretStr(env_var_replacement)

        secret_value_replacement = playbook_repo.key.get_secret_value()
        if is_base64_encoded(secret_value_replacement):
            playbook_repo.key = SecretStr(base64.b64decode(secret_value_replacement).decode("utf-8"))
        else:
            playbook_repo.key = SecretStr(secret_value_replacement)
        return playbook_repo

    @validator("global_config")
    def env_var_params(cls, global_config: dict):
        return replace_env_vars_values(global_config)
