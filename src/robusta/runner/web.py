import logging
from typing import List
from flask import Flask, request, jsonify
from pydantic import parse_obj_as

from ..core.model.events import ExecutionBaseEvent
from ..model.playbook_action import PlaybookAction
from ..integrations.prometheus.trigger import PrometheusTriggerEvent
from ..integrations.kubernetes.base_triggers import (
    IncomingK8sEventPayload,
    K8sTriggerEvent,
)
from ..integrations.vector.models import IncomingVectorPayload
from ..core.playbooks.playbooks_event_handler import PlaybooksEventHandler
from ..integrations.prometheus.models import AlertManagerEvent
from ..core.model.env_vars import NUM_EVENT_THREADS
from ..utils.task_queue import TaskQueue

app = Flask(__name__)


class Web:
    api_server_queue: TaskQueue
    alerts_queue: TaskQueue
    event_handler: PlaybooksEventHandler

    @staticmethod
    def init(event_handler: PlaybooksEventHandler):
        Web.api_server_queue = TaskQueue(
            name="api server queue", num_workers=NUM_EVENT_THREADS
        )
        Web.alerts_queue = TaskQueue(name="alerts queue", num_workers=NUM_EVENT_THREADS)
        Web.event_handler = event_handler

    @staticmethod
    def run():
        app.run(host="0.0.0.0", use_reloader=False)

    @staticmethod
    @app.route("/api/alerts", methods=["POST"])
    def handle_alert_event():
        alert_manager_event = AlertManagerEvent(**request.get_json())
        for alert in alert_manager_event.alerts:
            Web.alerts_queue.add_task(
                Web.event_handler.handle_trigger, PrometheusTriggerEvent(alert=alert)
            )
        return jsonify(success=True)

    @staticmethod
    @app.route("/api/vector", methods=["POST"])
    def handle_vector_log_event():
        matching_log_payloads = parse_obj_as(
            List[IncomingVectorPayload], request.get_json()
        )
        logging.debug(
            f"starting to run events for {len(matching_log_payloads)} log lines with files: "
            f"{set(x.file for x in matching_log_payloads)}"
        )
        for payload in matching_log_payloads:
            Web.__exec_async(payload)
        logging.debug(f"done running events for {len(matching_log_payloads)} log lines")
        return jsonify(success=True)

    @staticmethod
    @app.route("/api/handle", methods=["POST"])
    def handle_api_server_event():
        k8s_payload = IncomingK8sEventPayload(**request.get_json()["data"])
        Web.api_server_queue.add_task(
            Web.event_handler.handle_trigger, K8sTriggerEvent(k8s_payload=k8s_payload)
        )
        return jsonify(success=True)

    @staticmethod
    @app.route("/api/trigger", methods=["POST"])
    def handle_manual_trigger():
        data = request.get_json()
        if not data.get("action_name", None):
            msg = f"Illegal trigger request {data}"
            logging.error(msg)
            return {"success": False, "msg": msg}

        return jsonify(
            Web.event_handler.run_external_action(
                action_name=data["action_name"],
                action_params=data.get("action_params", None),
                sinks=data.get("sinks", None),
            )
        )
