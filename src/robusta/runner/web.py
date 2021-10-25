import json
import logging
from typing import List
from flask import Flask, request, jsonify
from pydantic import parse_obj_as

from ..core.model.events import ExecutionBaseEvent
from ..model.playbook_action import PlaybookAction
from ..core.playbooks.base_trigger import TriggerEvent
from ..integrations.prometheus.trigger import PrometheusTriggerEvent
from ..integrations.kubernetes.base_triggers import (
    IncomingK8sEventPayload,
    K8sTriggerEvent,
)
from ..integrations.vector.models import IncomingVectorPayload
from ..core.playbooks.playbooks_event_handler import PlaybooksEventHandler
from ..integrations.prometheus.models import AlertManagerEvent, PrometheusAlert
from ..core.model.env_vars import NUM_EVENT_THREADS
from ..utils.task_queue import TaskQueue

app = Flask(__name__)


class Web:
    task_queue: TaskQueue
    event_handler: PlaybooksEventHandler

    @staticmethod
    def init(event_handler: PlaybooksEventHandler):
        Web.task_queue = TaskQueue(num_workers=NUM_EVENT_THREADS)
        Web.event_handler = event_handler

    @staticmethod
    def __exec_async(trigger_event: TriggerEvent):
        Web.task_queue.add_task(Web.event_handler.handle_trigger, trigger_event)

    @staticmethod
    def run():
        app.run(host="0.0.0.0", use_reloader=False)

    @staticmethod
    @app.route("/api/alerts", methods=["POST"])
    def handle_alert_event():
        alert_manager_event = AlertManagerEvent(**request.get_json())
        for alert in alert_manager_event.alerts:
            Web.__exec_async(PrometheusTriggerEvent(alert=alert))
        return jsonify(success=True)

    @staticmethod
    @app.route("/api/vector", methods=["POST"])
    def handle_vector_log_event():
        matching_log_payloads = parse_obj_as(
            List[IncomingVectorPayload], request.get_json()
        )
        for payload in matching_log_payloads:
            Web.__exec_async(payload)
        return jsonify(success=True)

    @staticmethod
    @app.route("/api/handle", methods=["POST"])
    def handle_api_server_event():
        k8s_payload = IncomingK8sEventPayload(**request.get_json()["data"])
        Web.__exec_async(K8sTriggerEvent(k8s_payload=k8s_payload))
        return jsonify(success=True)

    @staticmethod
    @app.route("/api/trigger", methods=["POST"])
    def handle_manual_trigger():
        data = request.get_json()
        if not data.get("action_name", None):
            msg = f"Illegal trigger request {data}"
            logging.error(msg)
            return {"success": False, "msg": msg}

        playbook_action = PlaybookAction(
            action_name=data["action_name"],
            action_params=data.get("action_params", None),
        )
        execution_event = ExecutionBaseEvent(named_sinks=data.get("sinks", None))
        return jsonify(
            Web.event_handler.run_actions(execution_event, [playbook_action])
        )
