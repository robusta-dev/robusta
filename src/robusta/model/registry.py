from typing import List, Dict

from robusta.core.model.env_vars import RUNNER_VERSION, PROMETHEUS_ENABLED
from robusta.core.playbooks.actions_registry import ActionsRegistry
from robusta.integrations.receiver import ActionRequestReceiver
from robusta.integrations.scheduled.playbook_scheduler_manager import PlaybooksSchedulerManager
from robusta.model.config import PlaybooksRegistry, SinksRegistry
from robusta.model.registry_handler import RegistryHandler
from robusta.runner.telemetry import Telemetry


class Registry(RegistryHandler):
    _actions: ActionsRegistry = ActionsRegistry()
    _light_actions: List[str] = []
    _playbooks: PlaybooksRegistry = PlaybooksRegistry()
    _sinks: SinksRegistry = None
    _scheduler = None
    _receiver: ActionRequestReceiver = None
    _global_config = dict()
    _telemetry: Telemetry = Telemetry(
        runner_version=RUNNER_VERSION,
        prometheus_enabled=PROMETHEUS_ENABLED,
    )

    def set_light_actions(self, light_actions: List[str]):
        self._light_actions = light_actions

    def get_light_actions(self) -> List[str]:
        return self._light_actions

    def set_actions(self, actions: ActionsRegistry):
        self._actions = actions

    def get_actions(self) -> ActionsRegistry:
        return self._actions

    def set_playbooks(self, playbooks: PlaybooksRegistry):
        self._playbooks = playbooks

    def get_playbooks(self) -> PlaybooksRegistry:
        return self._playbooks

    def set_sinks(self, sinks: SinksRegistry):
        self._sinks = sinks

    def get_sinks(self) -> SinksRegistry:
        return self._sinks

    def set_scheduler(self, scheduler: PlaybooksSchedulerManager):
        self._scheduler = scheduler

    def get_scheduler(self) -> PlaybooksSchedulerManager:
        return self._scheduler

    def set_receiver(self, receiver: ActionRequestReceiver):
        self._receiver = receiver

    def get_receiver(self) -> ActionRequestReceiver:
        return self._receiver

    def get_telemetry(self) -> Telemetry:
        return self._telemetry

    def set_global_config(self, config: Dict):
        self.global_config = config

    def get_global_config(self) -> Dict:
        return self.global_config
