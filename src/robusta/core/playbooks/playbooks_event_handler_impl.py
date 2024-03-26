import copy
import logging
import sys
import time
import traceback
from collections import defaultdict
from typing import Any, Dict, List, Optional

import prometheus_client
from prometrix import PrometheusNotFound

from robusta.core.model.events import ExecutionBaseEvent, ExecutionContext
from robusta.core.playbooks.base_trigger import BaseTrigger, TriggerEvent
from robusta.core.playbooks.playbook_utils import merge_global_params, to_safe_str
from robusta.core.playbooks.playbooks_event_handler import PlaybooksEventHandler
from robusta.core.playbooks.trigger import Trigger
from robusta.core.reporting import MarkdownBlock
from robusta.core.reporting.base import Finding
from robusta.core.reporting.consts import SYNC_RESPONSE_SINK
from robusta.core.sinks.robusta.dal.model_conversion import ModelConversion
from robusta.integrations.kubernetes.base_triggers import K8sBaseTrigger
from robusta.model.alert_relabel_config import AlertRelabel
from robusta.model.config import Registry
from robusta.model.playbook_action import PlaybookAction
from robusta.runner.telemetry import Telemetry
from robusta.utils.error_codes import ActionException, ErrorCodes
from robusta.utils.stack_tracer import StackTracer

playbooks_errors_count = prometheus_client.Counter(
    "playbooks_errors", "Number of playbooks failures.", labelnames=("source",)
)
playbooks_summary = prometheus_client.Summary(
    "playbooks_process_time", "Total playbooks process time (seconds)", labelnames=("source",)
)


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
        build_context: Dict[str, Any] = {}
        for playbook in playbooks:
            fired_trigger = self.__get_fired_trigger(trigger_event, playbook.triggers, playbook.get_id(), build_context)
            if fired_trigger:
                execution_event = None
                try:
                    execution_event = fired_trigger.build_execution_event(trigger_event, sink_findings, build_context)
                    if isinstance(fired_trigger, K8sBaseTrigger):
                        if not fired_trigger.check_change_filters(execution_event):
                            continue
                    # sink_findings needs to be shared between playbooks.
                    # build_execution_event returns a different instance because it's running in a child process
                    execution_event.sink_findings = sink_findings
                except Exception:
                    logging.error(
                        f"Failed to build execution event for {trigger_event.get_event_description()}, Event: {trigger_event}",
                        exc_info=True,
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
                    if playbook_resp:  # For now, only last response applies. (For simplicity reasons)
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
            execution_event.named_sinks = self.registry.get_playbooks().get_default_sinks()

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
                self.__to_finding_json(finding) for finding in execution_event.sink_findings[SYNC_RESPONSE_SINK]
            ]

        return execution_response

    def __to_finding_json(self, finding: Finding) -> Dict:
        account_id = self.registry.get_global_config().get("account_id", "")
        cluster_id = self.registry.get_global_config().get("cluster_name", "")
        signing_key = self.registry.get_global_config().get("signing_key", "")

        finding_json = ModelConversion.to_finding_json(account_id, cluster_id, finding)

        finding_json["evidence"] = [
            ModelConversion.to_evidence_json(
                account_id, cluster_id, SYNC_RESPONSE_SINK, signing_key, finding.id, enrichment
            )
            for enrichment in finding.enrichments
        ]
        return finding_json

    def __prepare_execution_event(self, execution_event: ExecutionBaseEvent):
        execution_event.set_scheduler(self.registry.get_scheduler())
        execution_event.set_event_emitter(self.registry.get_event_emitter())
        execution_event.set_all_sinks(self.registry.get_sinks().get_all())
        execution_event.set_context(
            ExecutionContext(
                account_id=self.registry.get_global_config().get("account_id", ""),
                cluster_name=self.registry.get_global_config().get("cluster_name", ""),
            )
        )

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
            return self.__error_resp(f"External action not found {action_name}", ErrorCodes.ACTION_NOT_FOUND.value)

        if not action_def.from_params_func:
            return self.__error_resp(
                f"Action {action_name} cannot run using external event", ErrorCodes.NOT_EXTERNAL_ACTION.value
            )

        if not no_sinks and sinks:
            if action_params:
                action_params["named_sinks"] = sinks
            else:
                action_params = {"named_sinks": sinks}
        try:
            instantiation_params = action_def.from_params_parameter_class(**action_params)
        except Exception:
            return self.__error_resp(
                f"Failed to create execution instance for"
                f" {action_name} {action_def.from_params_parameter_class}"
                f" {action_params} {traceback.format_exc()}",
                ErrorCodes.EVENT_PARAMS_INSTANTIATION_FAILED.value,
            )

        execution_event = action_def.from_params_func(instantiation_params)
        if not execution_event:
            return self.__error_resp(
                f"Failed to create execution event for {action_name} {action_params}",
                ErrorCodes.EVENT_INSTANTIATION_FAILED.value,
            )

        playbook_action = PlaybookAction(action_name=action_name, action_params=action_params)
        return self.run_actions(execution_event, [playbook_action], sync_response, no_sinks)

    @classmethod
    def __error_resp(cls, msg: str, error_code: int, log: bool = True) -> dict:
        if log:
            logging.error(msg)
        return {"success": False, "msg": msg, "error_code": error_code}

    def __run_playbook_actions(
        self,
        execution_event: ExecutionBaseEvent,
        actions: List[PlaybookAction],
    ) -> Dict[str, Any]:
        start_time = time.time()
        source: str = (
            "manual_action"
            if any(name == SYNC_RESPONSE_SINK for name in getattr(execution_event, "named_sinks", []))
            else ""
        )
        self.__prepare_execution_event(execution_event)
        execution_event.response = {"success": True}
        for action in actions:
            if execution_event.stop_processing:
                return execution_event.response

            registered_action = self.registry.get_actions().get_action(action.action_name)

            if not registered_action:  # Might happen if manually trying to trigger incorrect action
                msg = f"action {action.action_name} not found. Skipping for event {type(execution_event)}"
                execution_event.response = self.__error_resp(msg, ErrorCodes.ACTION_NOT_REGISTERED.value)
                playbooks_errors_count.labels(source).inc()
                continue

            if not isinstance(execution_event, registered_action.event_type):
                msg = f"Action {action.action_name} requires {registered_action.event_type}"
                execution_event.response = self.__error_resp(msg, ErrorCodes.EXECUTION_EVENT_MISMATCH.value)
                playbooks_errors_count.labels(source).inc()
                continue

            action_with_params: bool = registered_action.params_type is not None
            action_params = None
            params = None
            if action_with_params:
                try:
                    action_params = merge_global_params(self.get_global_config(), action.action_params)
                    params = registered_action.params_type(**action_params)
                    params.post_initialization()
                except Exception:
                    msg = (
                        f"Failed to create {registered_action.params_type} "
                        f"using {to_safe_str(action_params)} for running {action.action_name} "
                        f"exc={traceback.format_exc()}"
                    )
                    execution_event.response = self.__error_resp(msg, ErrorCodes.PARAMS_INSTANTIATION_FAILED.value)
                    playbooks_errors_count.labels(source).inc()
                    continue
            try:
                if action_with_params:
                    registered_action.func(execution_event, params)
                else:
                    registered_action.func(execution_event)
            except ActionException as e:
                msg = (
                    e.msg
                    if e.msg
                    else f"Action Exception {e.type} while processing {action.action_name} {to_safe_str(action_params)}"
                )
                logging.error(msg)
                execution_event.response = self.__error_resp(e.type, e.code, log=False)
                playbooks_errors_count.labels(source).inc()
            except PrometheusNotFound as e:
                logging.error(str(e))

                if not execution_event.is_sink_findings_empty():
                    execution_event.add_enrichment(
                        [
                            MarkdownBlock(
                                text="Robusta couldn't connect to the Prometheus client, check if the service is "
                                "available. If it is, please add to *globalConfig* in *generated_values.yaml* "
                                "the cluster *prometheus_url*. For example:\n"
                                "```globalConfig:\n"
                                "\tprometheus_url: http://prometheus-server.monitoring.svc.cluster.local:9090```"
                            )
                        ]
                    )
                execution_event.response = self.__error_resp(
                    ErrorCodes.PROMETHEUS_DISCOVERY_FAILED.name, ErrorCodes.PROMETHEUS_DISCOVERY_FAILED.value, log=False
                )
                playbooks_errors_count.labels(source).inc()
            except Exception:
                logging.error(
                    f"Failed to execute action {action.action_name} {to_safe_str(action_params)}", exc_info=True
                )
                execution_event.response = self.__error_resp(
                    ErrorCodes.ACTION_UNEXPECTED_ERROR.name, ErrorCodes.ACTION_UNEXPECTED_ERROR.value, log=False
                )
                playbooks_errors_count.labels(source).inc()

            playbooks_summary.labels(source).observe(time.time() - start_time)
        return execution_event.response

    @classmethod
    def __get_fired_trigger(
        cls,
        trigger_event: TriggerEvent,
        playbook_triggers: List[Trigger],
        playbook_id: str,
        build_context: Dict[str, Any],
    ) -> Optional[BaseTrigger]:
        for trigger in playbook_triggers:
            if trigger.get().should_fire(trigger_event, playbook_id, build_context):
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
                        logging.error(f"sink {sink_name} not found. Skipping event finding {finding}")
                        continue

                    # only write the finding if is matching against the sink matchers
                    if sink.accepts(finding):
                        # create deep copy, so that iterating on one sink enrichments won't affect the others
                        # Each sink has a different findings, but enrichments are shared
                        finding_copy = copy.deepcopy(finding)
                        sink.write_finding(finding_copy, self.registry.get_sinks().platform_enabled)

                        sink_info = sinks_info[sink_name]
                        sink_info.type = sink.__class__.__name__
                        sink_info.findings_count += 1

                        if sink.params.stop:
                            return

                except Exception:  # Failure to send to one sink shouldn't fail all
                    logging.error(f"Failed to publish finding to sink {sink_name}", exc_info=True)

    def get_global_config(self) -> dict:
        return self.registry.get_global_config()

    def get_relabel_config(self) -> List[AlertRelabel]:
        return self.registry.get_relabel_config()

    def get_light_actions(self) -> List[str]:
        return self.registry.get_light_actions()

    def get_telemetry(self) -> Telemetry:
        return self.registry.get_telemetry()

    def is_healthy(
        self,
    ) -> bool:
        sinks_registry = self.registry.get_sinks()
        if not sinks_registry or not sinks_registry.get_all():
            return True
        return all(sink.is_healthy() for sink in sinks_registry.get_all().values())

    def set_cluster_active(self, active: bool):
        logging.info(f"Setting cluster active to {active}")
        for sink in self.registry.get_sinks().get_all().values():
            sink.set_cluster_active(active)

    def handle_sigint(self, sig, frame):
        logging.info("SIGINT handler called")

        if not self.is_healthy():  # dump stuck trace only when the runner is unhealthy
            StackTracer.dump()

        receiver = self.registry.get_receiver()
        if receiver is not None:
            receiver.stop()

        self.set_cluster_active(False)
        sys.exit(0)
