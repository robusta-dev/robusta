import logging
from collections import defaultdict
from pydantic.main import BaseModel
from typing import List, Dict, Optional

from ..integrations.scheduled.playbook_scheduler_manager import (
    PlaybooksSchedulerManager,
)
from .playbook_definition import PlaybookDefinition
from ..utils.function_hashes import get_function_hash
from ..core.playbooks.playbook_utils import merge_global_params
from ..core.sinks.sink_base import SinkBase
from ..core.playbooks.base_trigger import TriggerEvent
from ..core.playbooks.actions_registry import ActionsRegistry


class ActivePlaybooks(BaseModel):
    active_playbooks: List[PlaybookDefinition]


class RuntimeAction(BaseModel):
    action_name: str
    action_params: Dict


class SinksRegistry:
    sinks: Dict[str, SinkBase] = {}
    cluster_name: str
    default_sinks: List[str]

    def __init__(self, sinks: Dict[str, SinkBase]):
        self.sinks = sinks
        self.default_sinks = [sink.sink_name for sink in sinks.values() if sink.default]
        if not self.default_sinks:
            logging.warning(
                f"No default sinks defined. By default, actions results are ignored."
            )

    def get_sink_by_name(self, sink_name: str) -> Optional[SinkBase]:
        return self.sinks.get(sink_name)

    def get_all(self) -> Dict[str, SinkBase]:
        return self.sinks


class PlaybooksRegistry:
    def __init__(
        self,
        active_playbooks: List[PlaybookDefinition],
        actions_registry: ActionsRegistry,
        global_config: dict,
        default_sinks: List[str],
    ):
        self.default_sinks = default_sinks
        self.playbooks = defaultdict(list)
        self.global_config = global_config
        for playbook_def in active_playbooks:
            # Merge playbooks params with global params and default sinks
            if not playbook_def.sinks:
                playbook_def.sinks = default_sinks.copy()

            for action in playbook_def.get_actions():
                action_def = actions_registry.get_action(action.action_name)
                if not action_def:
                    msg = f"Action {action.action_name} not found. Will not be executed"
                    logging.error(msg)
                    raise Exception(msg)
                action.set_func_hash(get_function_hash(action_def.func))
                if action_def.params_type:  # action has params
                    action.action_params = merge_global_params(
                        global_config, action.action_params
                    )
                    if getattr(action_def.params_type, "pre_deploy_func", None):
                        for trigger in playbook_def.triggers:
                            action_params = action_def.params_type(
                                **action.action_params
                            )
                            action_params.pre_deploy_func(trigger.get())

                # validate that the action can be triggered by all playbooks triggers
                for trigger in playbook_def.triggers:
                    exec_event_type = trigger.get().get_execution_event_type()
                    if not issubclass(exec_event_type, action_def.event_type):
                        msg = f"Action {action_def.action_name} cannot be triggered by {exec_event_type}"
                        logging.error(msg)
                        raise Exception(msg)

            playbook_def.post_init()

            # add the playbook only once for each event.
            playbooks_trigger_events = set(
                [
                    trigger_definition.get().get_trigger_event()
                    for trigger_definition in playbook_def.triggers
                ]
            )
            for event in playbooks_trigger_events:
                self.playbooks[event].append(playbook_def)

    def get_playbooks(self, trigger_event: TriggerEvent) -> List[PlaybookDefinition]:
        return self.playbooks.get(trigger_event.get_event_name(), [])

    def get_default_sinks(self):
        return self.default_sinks

    def get_global_config(self) -> dict:
        return self.global_config


class Registry:
    _actions: ActionsRegistry
    _playbooks: PlaybooksRegistry
    _sinks: SinksRegistry = None
    _scheduler = None

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
