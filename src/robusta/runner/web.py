import hashlib
import logging
import threading
from datetime import datetime
from typing import List

from cachetools import TTLCache
from flask import Flask, abort, jsonify, request
from prometheus_client import make_wsgi_app
from werkzeug.middleware.dispatcher import DispatcherMiddleware

from robusta.clients.robusta_client import fetch_runner_info
from robusta.core.model.env_vars import NUM_EVENT_THREADS, PORT, TRACE_INCOMING_ALERTS, TRACE_INCOMING_REQUESTS, \
    PROCESSED_ALERTS_CACHE_TTL, PROCESSED_ALERTS_CACHE_MAX_SIZE, RUNNER_VERSION
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

    processed_alerts_cache = TTLCache(maxsize=PROCESSED_ALERTS_CACHE_MAX_SIZE, ttl=PROCESSED_ALERTS_CACHE_TTL)
    processed_alerts_cache_lock = threading.Lock()

    @staticmethod
    def init(event_handler: PlaybooksEventHandler, loader: ConfigLoader):
        Web.metrics = QueueMetrics()
        Web.api_server_queue = TaskQueue(name="api_server_queue", num_workers=NUM_EVENT_THREADS, metrics=Web.metrics)
        Web.alerts_queue = TaskQueue(name="alerts_queue", num_workers=NUM_EVENT_THREADS, metrics=Web.metrics)
        Web.event_handler = event_handler
        Web.loader = loader
        Web._check_version()

    @staticmethod
    def _check_version():
        runner_info = fetch_runner_info()
        if not runner_info or not runner_info.latest_version:
            # we couldn't fetch the latest version.
            return None
        
        if RUNNER_VERSION == "unknown":
            # Runner version is not set.
            return None
        
        if runner_info.latest_version == RUNNER_VERSION:
            return True
        
        logging.warning(
            "You are running version %s of robusta, but the latest version is %s. Please update to the latest version.",
            RUNNER_VERSION,
            runner_info.latest_version
        ) 
        return False


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
        Web._trace_incoming_alerts(req_json)
        alert_manager_event = AlertManagerEvent(**req_json)
        for alert in alert_manager_event.alerts:
            alert = Web._relabel_alert(alert)
            alert_hash = Web.get_compound_hash([
                alert.fingerprint.encode('ascii'),
                alert.status.encode('utf-8'),
                str(alert.startsAt.timestamp()).encode('ascii'),
                str(alert.endsAt.timestamp()).encode('ascii'),
            ])
            with Web.processed_alerts_cache_lock:
                if alert_hash in Web.processed_alerts_cache:
                    continue
                else:
                    Web.processed_alerts_cache[alert_hash] = True
            Web.alerts_queue.add_task(
                Web.event_handler.handle_trigger, PrometheusTriggerEvent(alert=alert)
            )

        Web.event_handler.get_telemetry().last_alert_at = str(datetime.now())
        return jsonify(success=True)

    @staticmethod
    def get_compound_hash(data: List[bytes]) -> bytes:
        hash_value = hashlib.sha1()
        for item in data:
            hash_value.update(hashlib.sha1(item).digest())
        return hash_value.digest()

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
                sync_response=data.get("sync_response", False),
                no_sinks=data.get("no_sinks", False),
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

    @staticmethod
    def _trace_incoming_alerts(incoming_request):
        """
        Enable to trace incoming AlertManager alerts
        """
        if TRACE_INCOMING_ALERTS:
            logging.info(f"Alerts: \n{incoming_request}\n")
