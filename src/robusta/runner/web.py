import logging
from datetime import datetime
from flask import Flask, request, jsonify
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from prometheus_client import make_wsgi_app

from .config_loader import ConfigLoader
from ..integrations.prometheus.trigger import PrometheusTriggerEvent
from ..integrations.kubernetes.base_triggers import (
    IncomingK8sEventPayload,
    K8sTriggerEvent,
)
from ..core.playbooks.playbooks_event_handler import PlaybooksEventHandler
from ..integrations.prometheus.models import AlertManagerEvent
from ..core.model.env_vars import NUM_EVENT_THREADS
from ..utils.task_queue import TaskQueue, QueueMetrics

app = Flask(__name__)
app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {"/metrics": make_wsgi_app()})


class Web:
    api_server_queue: TaskQueue
    alerts_queue: TaskQueue
    event_handler: PlaybooksEventHandler
    metrics: QueueMetrics
    loader: ConfigLoader


    @staticmethod
    def init(event_handler: PlaybooksEventHandler, loader: ConfigLoader):
        Web.metrics = QueueMetrics()
        Web.api_server_queue = TaskQueue(
            name="api server queue", num_workers=NUM_EVENT_THREADS, metrics=Web.metrics
        )
        Web.alerts_queue = TaskQueue(
            name="alerts queue", num_workers=NUM_EVENT_THREADS, metrics=Web.metrics
        )
        Web.event_handler = event_handler
        Web.loader = loader


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
        
        Web.event_handler.get_telemetry().last_alert_at = str(datetime.now())
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

    @staticmethod
    @app.route("/api/playbooks/reload", methods=["POST"])
    def handle_playbooks_reload():
        Web.loader.reload("reload request")
        return jsonify(success=True)
