import logging
from datetime import datetime

from flask import Flask, abort, jsonify, request
from prometheus_client import make_wsgi_app
from werkzeug.middleware.dispatcher import DispatcherMiddleware

from robusta.core.model.env_vars import NUM_EVENT_THREADS, PORT, TRACE_INCOMING_REQUESTS
from robusta.core.playbooks.playbooks_event_handler import PlaybooksEventHandler
from robusta.core.triggers.helm_releases_triggers import HelmReleasesTriggerEvent, IncomingHelmReleasesEventPayload
from robusta.integrations.kubernetes.base_triggers import IncomingK8sEventPayload, K8sTriggerEvent
from robusta.integrations.prometheus.models import AlertManagerEvent, PrometheusAlert
from robusta.integrations.prometheus.trigger import PrometheusTriggerEvent
from robusta.model.alert_relabel_config import AlertRelabelOp
from robusta.runner.config_loader import ConfigLoader
from robusta.utils.task_queue import QueueMetrics, TaskQueue

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
        Web.api_server_queue = TaskQueue(name="api_server_queue", num_workers=NUM_EVENT_THREADS, metrics=Web.metrics)
        Web.alerts_queue = TaskQueue(name="alerts_queue", num_workers=NUM_EVENT_THREADS, metrics=Web.metrics)
        Web.event_handler = event_handler
        Web.loader = loader

    @staticmethod
    def run():
        app.run(host="0.0.0.0", port=PORT, use_reloader=False)

    @classmethod
    def _relabel_alert(cls, alert: PrometheusAlert) -> PrometheusAlert:
        for relabel in cls.event_handler.get_relabel_config():
            source_value = alert.labels.get(relabel.source, None)
            if source_value:
                alert.labels[relabel.target] = source_value
                if relabel.operation == AlertRelabelOp.Replace:
                    del alert.labels[relabel.source]

        return alert

    @staticmethod
    @app.route("/api/alerts", methods=["POST"])
    def handle_alert_event():
        req_json = request.get_json()
        Web._trace_incoming("alerts", req_json)
        alert_manager_event = AlertManagerEvent(**req_json)
        for alert in alert_manager_event.alerts:
            alert = Web._relabel_alert(alert)
            Web.alerts_queue.add_task(Web.event_handler.handle_trigger, PrometheusTriggerEvent(alert=alert))

        Web.event_handler.get_telemetry().last_alert_at = str(datetime.now())
        return jsonify(success=True)

    @staticmethod
    @app.route("/api/helm-releases", methods=["POST"])
    def handle_helm_releases():
        req_json = request.get_json()
        Web._trace_incoming("received helm release trigger events via api", req_json)
        logging.debug("received helm release trigger events via api\n")
        helm_release_payload = IncomingHelmReleasesEventPayload.parse_obj(req_json)
        for helm_release in helm_release_payload.data:
            Web.api_server_queue.add_task(
                Web.event_handler.handle_trigger, HelmReleasesTriggerEvent(helm_release=helm_release)
            )
        return jsonify(success=True)

    @staticmethod
    @app.route("/api/handle", methods=["POST"])
    def handle_api_server_event():
        data = request.get_json()["data"]
        Web._trace_incoming("api server", data)
        k8s_payload = IncomingK8sEventPayload(**data)
        Web.api_server_queue.add_task(Web.event_handler.handle_trigger, K8sTriggerEvent(k8s_payload=k8s_payload))
        return jsonify(success=True)

    @staticmethod
    @app.route("/api/trigger", methods=["POST"])
    def handle_manual_trigger():
        data = request.get_json()
        Web._trace_incoming("trigger", data)
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

    @staticmethod
    @app.route("/healthz", methods=["GET"])
    def healthz():
        if Web.event_handler.is_healthy():
            return jsonify()
        else:
            logging.error("Runner health check failed")
            return abort(status=500, code=500)

    @staticmethod
    def _trace_incoming(api: str, incoming_request):
        """
        Used for Robusta development purposes
        Sometimes, it's useful to view incoming requests payload, whether it's AlertManager alerts,
        API server events or any other data source
        """
        if TRACE_INCOMING_REQUESTS:
            logging.info(f"{api}: {incoming_request}")
