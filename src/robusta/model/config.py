import logging
from collections import defaultdict
from typing import List, Dict, Optional

from ..core.sinks.robusta.robusta_sink_params import RobustaSinkConfigWrapper, RobustaSinkParams
from ..core.sinks.sink_config import SinkConfigBase
from ..core.sinks.sink_factory import SinkFactory
from ..integrations.scheduled.playbook_scheduler_manager import (
    PlaybooksSchedulerManager,
)
from ..integrations.receiver import ActionRequestReceiver
from .playbook_definition import PlaybookDefinition
from ..utils.function_hashes import get_function_hash
from ..core.playbooks.playbook_utils import merge_global_params
from ..core.sinks.sink_base import SinkBase
from ..core.playbooks.base_trigger import TriggerEvent
from ..core.playbooks.actions_registry import ActionsRegistry
from ..runner.telemetry import Telemetry
from ..core.model.env_vars import RUNNER_VERSION, PROMETHEUS_ENABLED



class SinksRegistry:

    def __init__(self, sinks: Dict[str, SinkBase]):
        self.sinks = sinks
        self.default_sinks = [sink.sink_name for sink in sinks.values() if sink.default]
        if not self.default_sinks:
            logging.warning(
                f"No default sinks defined. By default, actions results are ignored."
            )
        platform_sinks = [sink for sink in sinks.values() if isinstance(sink.params, RobustaSinkParams)]
        self.platform_enabled = len(platform_sinks) > 0

    def get_sink_by_name(self, sink_name: str) -> Optional[SinkBase]:
        return self.sinks.get(sink_name)

    def get_all(self) -> Dict[str, SinkBase]:
        return self.sinks

    @classmethod
    def construct_new_sinks(
        cls,
        new_sinks_config: List[SinkConfigBase],
        existing_sinks: Dict[str, SinkBase],
        registry
    ) -> Dict[str, SinkBase]:
    
        new_sink_names = [sink_config.get_name() for sink_config in new_sinks_config]
        # remove deleted sinks
        deleted_sink_names = [
            sink_name
            for sink_name in existing_sinks.keys()
            if sink_name not in new_sink_names
        ]
        for deleted_sink in deleted_sink_names:
            logging.info(f"Deleting sink {deleted_sink}")
            existing_sinks[deleted_sink].stop()
            del existing_sinks[deleted_sink]

        new_sinks = existing_sinks.copy()
        # create new sinks, or update existing if changed
        for sink_config in new_sinks_config:
            try:
                # temporary workaround to skip the default and unconfigured robusta token
                if (
                    isinstance(sink_config, RobustaSinkConfigWrapper)
                    and sink_config.robusta_sink.token == "<ROBUSTA_ACCOUNT_TOKEN>"
                ):
                    continue
                if sink_config.get_name() not in new_sinks.keys():
                    logging.info(
                        f"Adding {type(sink_config)} sink named {sink_config.get_name()}"
                    )
                    new_sinks[sink_config.get_name()] = SinkFactory.create_sink(
                        sink_config, registry
                    )
                elif (
                    sink_config.get_params() != new_sinks[sink_config.get_name()].params
                ):
                    logging.info(
                        f"Updating {type(sink_config)} sink named {sink_config.get_name()}"
                    )
                    new_sinks[sink_config.get_name()].stop()
                    new_sinks[sink_config.get_name()] = SinkFactory.create_sink(
                        sink_config, registry
                    )
            except Exception as e:
                logging.error(
                    f"Error configuring sink {sink_config.get_name()} of type {type(sink_config)}: {e}"
                )

        return new_sinks


class PlaybooksRegistry:
    def get_playbooks(self, trigger_event: TriggerEvent) -> List[PlaybookDefinition]:
        return []

    def get_default_sinks(self):
        return []

    def get_global_config(self) -> dict:
        return {}


class PlaybooksRegistryImpl(PlaybooksRegistry):
    def __init__(
        self,
        active_playbooks: List[PlaybookDefinition],
        actions_registry: ActionsRegistry,
        global_config: dict,
        default_sinks: List[str],
    ):
        self.default_sinks = default_sinks
        self.triggers_to_playbooks = defaultdict(list)
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
                self.triggers_to_playbooks[event].append(playbook_def)

    def get_playbooks(self, trigger_event: TriggerEvent) -> List[PlaybookDefinition]:
        return self.triggers_to_playbooks.get(trigger_event.get_event_name(), [])

    def get_default_sinks(self) -> List[str]:
        return self.default_sinks

    def get_global_config(self) -> dict:
        return self.global_config


class Registry:
    _actions: ActionsRegistry = ActionsRegistry()
    _playbooks: PlaybooksRegistry = PlaybooksRegistry()
    _sinks: SinksRegistry = None
    _scheduler = None
    _receiver: ActionRequestReceiver = None
    _global_config = dict()
    _telemetry: Telemetry = Telemetry(
        runner_version=RUNNER_VERSION,
        prometheus_enabled=PROMETHEUS_ENABLED, 
    )

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

    def set_global_config(self, config : Dict ):
        self.global_config = config
    
    def get_global_config(self) -> Dict:
        return self.global_config
