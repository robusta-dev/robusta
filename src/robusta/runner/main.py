import logging
import os
import os.path
from inspect import getmembers

import colorlog
import manhole
from flask import Flask, request

from ..core.model.cloud_event import CloudEvent
from .. import api as robusta_api
from ..core.active_playbooks import run_playbooks
from ..core.persistency.scheduled_jobs_states_dal import init_scheduler_dal
from ..integrations.prometheus.incoming_handler import parse_incoming_prometheus_alerts
from ..integrations.manual.incoming_handler import parse_incoming_manual_trigger
from ..integrations.slack.receiver import start_slack_receiver
from .config_handler import ConfigHandler
from ..integrations.scheduled.triggers import init_scheduler


app = Flask(__name__)

LOGGING_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
LOGGING_FORMAT = "%(log_color)s%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s"
LOGGING_DATEFMT = "%Y-%m-%d %H:%M:%S"

if os.environ.get("ENABLE_COLORED_LOGS", "false").lower() == "true":
    print("setting up colored logging")
    colorlog.basicConfig(
        format=LOGGING_FORMAT, level=LOGGING_LEVEL, datefmt=LOGGING_DATEFMT
    )
else:
    print("setting up regular logging")
    logging.basicConfig(
        format=LOGGING_FORMAT, level=LOGGING_LEVEL, datefmt=LOGGING_DATEFMT
    )

logging.getLogger().setLevel(LOGGING_LEVEL)
log = logging.getLogger("werkzeug")
log.setLevel(logging.ERROR)
logging.info(f"logger initialized using {LOGGING_LEVEL} log level")


def main():
    config_handler = ConfigHandler()
    if os.environ.get("ENABLE_MANHOLE", "false").lower() == "true":
        manhole.install(locals=dict(getmembers(robusta_api)))
    start_slack_receiver()
    init_scheduler_dal()
    init_scheduler()
    app.run(host="0.0.0.0", use_reloader=False)
    config_handler.close()


# TODO: in each of the below handlers we block until the playbook finishes running
# this is probably wrong especially if a playbook runs for some time
@app.route("/api/alerts", methods=["POST"])
def handle_alert_event():
    cloud_event = parse_incoming_prometheus_alerts(request)
    run_playbooks(cloud_event)
    return "OK"


@app.route("/api/handle", methods=["POST"])
def handle_cloud_event():
    cloud_event = CloudEvent(**request.get_json())
    run_playbooks(cloud_event)
    return "OK"


@app.route("/api/trigger", methods=["POST"])
def handle_manual_trigger():
    cloud_event = parse_incoming_manual_trigger(request)
    run_playbooks(cloud_event)
    return "OK"


if __name__ == "__main__":
    main()
