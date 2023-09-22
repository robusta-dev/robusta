import json
import os

import pytz


def load_bool(env_var, default: bool):
    s = os.environ.get(env_var, str(default))
    return json.loads(s.lower())


ROBUSTA_LOGO_URL = os.environ.get("ROBUSTA_LOGO_URL", "https://docs.robusta.dev/master/_static/robusta-logo.png")
PLAYBOOKS_ROOT = os.environ.get("PLAYBOOKS_ROOT", "/etc/robusta/playbooks/")
# should be the same as the one in out Dockerfile
DEFAULT_PLAYBOOKS_ROOT = os.environ.get("DEFAULT_PLAYBOOKS_ROOT", os.path.join(PLAYBOOKS_ROOT, "defaults"))
# when developing playbooks, we want to install it using pip. Otherwise no need because it's pre baked into the image
DEFAULT_PLAYBOOKS_PIP_INSTALL = load_bool("DEFAULT_PLAYBOOKS_PIP_INSTALL", False)

CUSTOM_PLAYBOOKS_ROOT = os.path.join(PLAYBOOKS_ROOT, "storage")

PLAYBOOKS_CONFIG_FILE_PATH = os.environ.get("PLAYBOOKS_CONFIG_FILE_PATH")

INSTALLATION_NAMESPACE = os.environ.get("INSTALLATION_NAMESPACE", "robusta")
DISCOVERY_PERIOD_SEC = int(os.environ.get("DISCOVERY_PERIOD_SEC", 90))
CLUSTER_STATUS_PERIOD_SEC = int(os.environ.get("CLUSTER_STATUS_PERIOD_SEC", 60 * 15))  # 15 min
DISCOVERY_CHECK_THRESHOLD_SEC = int(os.environ.get("DISCOVERY_CHECK_THRESHOLD_SEC", 60 * 50))  # 50 min
DISCOVERY_PROCESS_TIMEOUT_SEC = int(os.environ.get("DISCOVERY_PROCESS_TIMEOUT_SEC", 60 * 120))  # 120 min
DISCOVERY_WATCHDOG_CHECK_SEC = int(os.environ.get("DISCOVERY_WATCHDOG_CHECK_SEC", 15 * 120))  # 15 min
SUPABASE_LOGIN_RATE_LIMIT_SEC = int(os.environ.get("SUPABASE_LOGIN_RATE_LIMIT_SEC", 900))
SUPABASE_TIMEOUT_SECONDS = int(os.environ.get("SUPABASE_TIMEOUT_SECONDS", 60))
GRAFANA_RENDERER_URL = os.environ.get("GRAFANA_RENDERER_URL", "http://127.0.0.1:8281/render")
RESOURCE_UPDATES_CACHE_TTL_SEC = os.environ.get("RESOURCE_UPDATES_CACHE_TTL_SEC", 120)
INTERNAL_PLAYBOOKS_ROOT = os.environ.get("INTERNAL_PLAYBOOKS_ROOT", "/app/src/robusta/core/playbooks/internal")
DEFAULT_TIMEZONE = pytz.timezone(os.environ.get("DEFAULT_TIMEZONE", "UTC"))
NUM_EVENT_THREADS = int(os.environ.get("NUM_EVENT_THREADS", 20))
INCOMING_EVENTS_QUEUE_MAX_SIZE = int(os.environ.get("INCOMING_EVENTS_QUEUE_MAX_SIZE", 500))
ALERT_BUILDER_WORKERS = int(os.environ.get("ALERT_BUILDER_WORKERS", 5))
ALERTS_WORKERS_POOL = load_bool("ALERTS_WORKERS_POOL", False)

FLOAT_PRECISION_LIMIT = int(os.environ.get("FLOAT_PRECISION_LIMIT", 11))

PROMETHEUS_REQUEST_TIMEOUT_SECONDS = float(os.environ.get("PROMETHEUS_REQUEST_TIMEOUT_SECONDS", 90.0))
PROMETHEUS_ENABLED = os.environ.get("PROMETHEUS_ENABLED", "false").lower() == "true"
MANAGED_PROMETHEUS_ALERTS_ENABLED = os.environ.get("MANAGED_PROMETHEUS_ALERTS_ENABLED", "false").lower() == "true"
PROMETHEUS_SSL_ENABLED = os.environ.get("PROMETHEUS_SSL_ENABLED", "false").lower() == "true"

INCOMING_REQUEST_TIME_WINDOW_SECONDS = int(os.environ.get("INCOMING_REQUEST_TIME_WINDOW_SECONDS", 3600))

RELAY_EXTERNAL_ACTIONS_URL = os.environ.get(
    "RELAY_EXTERNAL_ACTIONS_URL", "https://api.robusta.dev/integrations/generic/actions"
)

GIT_MAX_RETRIES = int(os.environ.get("GIT_MAX_RETRIES", 100))

PRINTED_TABLE_MAX_WIDTH = int(os.environ.get("PRINTED_TABLE_MAX_WIDTH", 70))

RUNNER_VERSION = os.environ.get("RUNNER_VERSION", "unknown")

GRAFANA_READ_TIMEOUT = int(os.environ.get("GRAFANA_READ_TIMEOUT", 20))

TEAMS_IMAGE_WIDTH = os.environ.get("TEAMS_IMAGE_WIDTH", "700px")

ROBUSTA_UI_DOMAIN = os.environ.get("ROBUSTA_UI_DOMAIN", "https://platform.robusta.dev")

ROBUSTA_TELEMETRY_ENDPOINT = os.environ.get("ROBUSTA_TELEMETRY_ENDPOINT", "https://api.robusta.dev/telemetry")
ENABLE_TELEMETRY = os.environ.get("ENABLE_TELEMETRY", "true").lower() == "true"
SEND_ADDITIONAL_TELEMETRY = os.environ.get("SEND_ADDITIONAL_TELEMETRY", "false").lower() == "true"
RELEASE_NAME = os.environ.get("RELEASE_NAME", "robusta")

TELEMETRY_PERIODIC_SEC = int(os.environ.get("TELEMETRY_PERIODIC_SEC", 60 * 60 * 24))  # 24H

SLACK_TABLE_COLUMNS_LIMIT = int(os.environ.get("SLACK_TABLE_COLUMNS_LIMIT", 3))
DISCORD_TABLE_COLUMNS_LIMIT = int(os.environ.get("DISCORD_TABLE_COLUMNS_LIMIT", 4))
RSA_KEYS_PATH = os.environ.get("RSA_KEYS_PATH", "/etc/robusta/auth")

# default of 120 seconds was chosen, because we saw some disconnections after 6 minutes. We needed a lower interval
WEBSOCKET_PING_INTERVAL = int(os.environ.get("WEBSOCKET_PING_INTERVAL", 120))
# Timeout for the ping response, before killing the connection. Must be smaller than the interval
WEBSOCKET_PING_TIMEOUT = int(os.environ.get("WEBSOCKET_PING_TIMEOUT", 30))

TRACE_INCOMING_REQUESTS = load_bool("TRACE_INCOMING_REQUESTS", False)

SERVICE_CACHE_TTL_SEC = int(os.environ.get("SERVICE_CACHE_TTL_SEC", 900))
SERVICE_CACHE_MAX_SIZE = int(os.environ.get("SERVICE_CACHE_MAX_SIZE", 1000))

PORT = int(os.environ.get("PORT", 5000))  # PORT

# additional certificate to verify, base64 encoded.
ADDITIONAL_CERTIFICATE: str = os.environ.get("CERTIFICATE", "")

DISCOVERY_MAX_BATCHES = int(os.environ.get("DISCOVERY_MAX_BATCHES", 25))
DISCOVERY_BATCH_SIZE = int(os.environ.get("DISCOVERY_BATCH_SIZE", 2000))
DISCOVERY_POD_OWNED_PODS = load_bool("DISCOVERY_POD_OWNED_PODS", False)

DISABLE_HELM_MONITORING = load_bool("DISABLE_HELM_MONITORING", False)

PROMETHEUS_ERROR_LOG_PERIOD_SEC = int(os.environ.get("DISCOVERY_MAX_BATCHES", 14400))

RRM_PERIOD_SEC = int(os.environ.get("RRM_PERIOD_SEC", 90))

MAX_ALLOWED_RULES_PER_CRD_ALERT = int(os.environ.get("MAX_ALLOWED_RULES_PER_CRD_ALERT", 600))
