import copy
import logging
import traceback
from collections import defaultdict
from typing import Any, Dict, Optional, List

from .base_trigger import TriggerEvent, BaseTrigger
from .playbook_utils import merge_global_params, to_safe_str
from .playbooks_event_handler import PlaybooksEventHandler
from ..model.events import ExecutionBaseEvent, ExecutionContext
from ..reporting import MarkdownBlock
from ..reporting.base import Finding
from ..reporting.consts import SYNC_RESPONSE_SINK
from ..sinks.robusta.dal.model_conversion import ModelConversion
from ...model.playbook_action import PlaybookAction
from ...model.config import Registry
from .trigger import Trigger
from ...runner.telemetry import Telemetry


class PlaybooksEventHandlerImpl(PlaybooksEventHandler):
    def __init__(self, registry: Registry):
        self.registry = registry

    def handle_trigger(self, trigger_event: TriggerEvent) -> Optional[Dict[str, Any]]:
        playbooks = self.registry.get_playbooks().get_playbooks(trigger_event)
        if not playbooks:  # no registered playbooks for this event type
            return

        execution_response = None
        execution_event: Optional[ExecutionBaseEvent] = None
        sink_findings: Dict[str, List[Finding]] = defaultdict(list)
        for playbook in playbooks:
            fired_trigger = self.__get_fired_trigger(
                trigger_event, playbook.triggers, playbook.get_id()
            )
            if fired_trigger:
                execution_event = fired_trigger.build_execution_event(
                    trigger_event, sink_findings
                )
                if execution_event:  # might not exist for unsupported k8s types
                    execution_event.named_sinks = (
                        playbook.sinks
                        if playbook.sinks is not None
                        else self.registry.get_playbooks().get_default_sinks()
                    )

                    playbook_resp = self.__run_playbook_actions(
                        execution_event,
                        playbook.get_actions(),
                    )
                    if (
                        playbook_resp
                    ):  # For now, only last response applies. (For simplicity reasons)
                        execution_response = playbook_resp
                    if playbook.stop or execution_event.stop_processing:
                        break

        if execution_event:
            self.__handle_findings(execution_event)

        return execution_response

    def run_actions(
        self,
        execution_event: ExecutionBaseEvent,
        actions: List[PlaybookAction],
        sync_response: bool = False,
        no_sinks: bool = False,
    ) -> Optional[Dict[str, Any]]:
        if not no_sinks and execution_event.named_sinks is None:  # take the default sinks only if sinks not excluded
            execution_event.named_sinks = (
                self.registry.get_playbooks().get_default_sinks()
            )

        if sync_response:  # if we need to return sync response, we'll collect the findings under this sink name
            if execution_event.named_sinks:
                execution_event.named_sinks.append(SYNC_RESPONSE_SINK)
            else:
                execution_event.named_sinks = [SYNC_RESPONSE_SINK]

        execution_response = self.__run_playbook_actions(
            execution_event,
            actions,
        )
        self.__handle_findings(execution_event)

        if sync_response:  # add the findings to the response
            execution_response["findings"] = [
                self.__to_finding_json(finding)
                for finding in execution_event.sink_findings[SYNC_RESPONSE_SINK]
            ]

        return execution_response

    def __to_finding_json(self, finding: Finding) -> Dict:
        account_id = self.registry.get_global_config().get("account_id", "")
        cluster_id = self.registry.get_global_config().get("cluster_name", "")
        signing_key = self.registry.get_global_config().get("signing_key", "")

        finding_json = ModelConversion.to_finding_json(account_id, cluster_id, finding)

        finding_json["evidence"] = [
            ModelConversion.to_evidence_json(
                account_id,
                cluster_id,
                SYNC_RESPONSE_SINK,
                signing_key,
                finding.id,
                enrichment
            )
            for enrichment in finding.enrichments
        ]
        return finding_json

    def __prepare_execution_event(self, execution_event: ExecutionBaseEvent):
        execution_event.set_scheduler(self.registry.get_scheduler())
        execution_event.set_context(ExecutionContext(
            account_id=self.registry.get_global_config().get("account_id", ""),
            cluster_name=self.registry.get_global_config().get("cluster_name", "")
        ))

    def run_external_action(
        self,
        action_name: str,
        action_params: Optional[dict],
        sinks: Optional[List[str]],
        sync_response: bool = False,
        no_sinks: bool = False,
    ) -> Optional[Dict[str, Any]]:
        action_def = self.registry.get_actions().get_action(action_name)
        if not action_def:
            return self.__error_resp(f"External action not found {action_name}")

        if not action_def.from_params_func:
            return self.__error_resp(
                f"Action {action_name} cannot run using external event"
            )

        if not no_sinks and sinks:
            if action_params:
                action_params["named_sinks"] = sinks
            else:
                action_params = {"named_sinks": sinks}
        try:
            instantiation_params = action_def.from_params_parameter_class(
                **action_params
            )
        except Exception:
            return self.__error_resp(
                f"Failed to create execution instance for"
                f" {action_name} {action_def.from_params_parameter_class}"
                f" {action_params} {traceback.format_exc()}"
            )

        execution_event = action_def.from_params_func(instantiation_params)
        if not execution_event:
            return self.__error_resp(
                f"Failed to create execution event for "
                f"{action_name} {action_params}"
            )

        playbook_action = PlaybookAction(
            action_name=action_name, action_params=action_params
        )
        return self.run_actions(execution_event, [playbook_action], sync_response, no_sinks)

    @classmethod
    def __error_resp(cls, msg: str) -> dict:
        logging.error(msg)
        return {"success": False, "msg": msg}

    def __run_playbook_actions(
        self,
        execution_event: ExecutionBaseEvent,
        actions: List[PlaybookAction],
    ) -> Dict[str, Any]:
        self.__prepare_execution_event(execution_event)
        execution_event.response = {"success": True}
        for action in actions:
            if execution_event.stop_processing:
                return execution_event.response

            registered_action = self.registry.get_actions().get_action(
                action.action_name
            )

            if (
                not registered_action
            ):  # Might happen if manually trying to trigger incorrect action
                msg = f"action {action.action_name} not found. Skipping for event {type(execution_event)}"
                execution_event.response = self.__error_resp(msg)
                continue

            if not isinstance(execution_event, registered_action.event_type):
                msg = f"Action {action.action_name} requires {registered_action.event_type}"
                execution_event.response = self.__error_resp(msg)
                continue

            if not registered_action.params_type:
                registered_action.func(execution_event)
            else:
                action_params = None
                try:
                    action_params = merge_global_params(
                        self.get_global_config(), action.action_params
                    )
                    params = registered_action.params_type(**action_params)
                except Exception:
                    msg = (
                        f"Failed to create {registered_action.params_type} "
                        f"using {to_safe_str(action_params)} for running {action.action_name} "
                        f"exc={traceback.format_exc()}"
                    )
                    execution_event.response = self.__error_resp(msg)
                    continue

                try:
                    registered_action.func(execution_event, params)
                except Exception:
                    logging.error(
                        f"Failed to execute action {action.action_name} {to_safe_str(action_params)}",
                        exc_info=True,
                    )
                    execution_event.add_enrichment(
                        [
                            MarkdownBlock(
                                text=f"Oops... Error processing {action.action_name}"
                            )
                        ]
                    )

        return execution_event.response

    @classmethod
    def __get_fired_trigger(
        cls,
        trigger_event: TriggerEvent,
        playbook_triggers: List[Trigger],
        playbook_id: str,
    ) -> Optional[BaseTrigger]:
        for trigger in playbook_triggers:
            if trigger.get().should_fire(trigger_event, playbook_id):
                return trigger.get()
        return None

    def __handle_findings(self, execution_event: ExecutionBaseEvent):
        sinks_info = self.registry.get_telemetry().sinks_info

        for sink_name in execution_event.sink_findings.keys():
            if SYNC_RESPONSE_SINK == sink_name:
                continue  # not a real sink, just container for findings that needs to be returned synchronously

            for finding in execution_event.sink_findings[sink_name]:
                try:
                    sink = self.registry.get_sinks().sinks.get(sink_name)
                    if not sink:
                        logging.error(
                            f"sink {sink_name} not found. Skipping event finding {finding}"
                        )
                        continue

                    # only write the finding if is matching against the sink matchers
                    if sink.accepts(finding):
                        # create deep copy, so that iterating on one sink enrichments won't affect the others
                        # Each sink has a different findings, but enrichments are shared
                        finding_copy = copy.deepcopy(finding)
                        sink.write_finding(
                            finding_copy, self.registry.get_sinks().platform_enabled
                        )
                        
                        sink_info = sinks_info[sink_name]
                        sink_info.type = sink.__class__.__name__
                        sink_info.findings_count += 1

                except Exception:  # Failure to send to one sink shouldn't fail all
                    logging.error(
                        f"Failed to publish finding to sink {sink_name}", exc_info=True
                    )

    def get_global_config(self) -> dict:
        return self.registry.get_playbooks().get_global_config()

    def get_telemetry(self) -> Telemetry:
        return self.registry.get_telemetry()
