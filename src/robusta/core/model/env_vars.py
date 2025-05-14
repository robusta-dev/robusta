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
CUSTOM_SSH_HOST_KEYS = os.environ.get("CUSTOM_SSH_HOST_KEYS", "")

PLAYBOOKS_CONFIG_FILE_PATH = os.environ.get("PLAYBOOKS_CONFIG_FILE_PATH")

INSTALLATION_NAMESPACE = os.environ.get("INSTALLATION_NAMESPACE", "robusta")
DISCOVERY_PERIOD_SEC = int(os.environ.get("DISCOVERY_PERIOD_SEC", 90))
CLUSTER_STATUS_PERIOD_SEC = int(os.environ.get("CLUSTER_STATUS_PERIOD_SEC", 60 * 15))  # 15 min
DISCOVERY_CHECK_THRESHOLD_SEC = int(os.environ.get("DISCOVERY_CHECK_THRESHOLD_SEC", 60 * 50))  # 50 min
DISCOVERY_PROCESS_TIMEOUT_SEC = int(os.environ.get("DISCOVERY_PROCESS_TIMEOUT_SEC", 60 * 120))  # 120 min
DISCOVERY_WATCHDOG_CHECK_SEC = int(os.environ.get("DISCOVERY_WATCHDOG_CHECK_SEC", 15 * 120))  # 15 min
SUPABASE_TIMEOUT_SECONDS = int(os.environ.get("SUPABASE_TIMEOUT_SECONDS", 60))
GRAFANA_RENDERER_URL = os.environ.get("GRAFANA_RENDERER_URL", "http://127.0.0.1:8281/render")
RESOURCE_UPDATES_CACHE_TTL_SEC = os.environ.get("RESOURCE_UPDATES_CACHE_TTL_SEC", 120)
INTERNAL_PLAYBOOKS_ROOT = os.environ.get("INTERNAL_PLAYBOOKS_ROOT", "/app/src/robusta/core/playbooks/internal")
DEFAULT_TIMEZONE = pytz.timezone(os.environ.get("DEFAULT_TIMEZONE", "UTC"))
NUM_EVENT_THREADS = int(os.environ.get("NUM_EVENT_THREADS", 20))
INCOMING_EVENTS_QUEUE_MAX_SIZE = int(os.environ.get("INCOMING_EVENTS_QUEUE_MAX_SIZE", 500))

FLOAT_PRECISION_LIMIT = int(os.environ.get("FLOAT_PRECISION_LIMIT", 11))

PROMETHEUS_REQUEST_TIMEOUT_SECONDS = float(os.environ.get("PROMETHEUS_REQUEST_TIMEOUT_SECONDS", 90.0))
PROMETHEUS_ENABLED = os.environ.get("PROMETHEUS_ENABLED", "false").lower() == "true"
MANAGED_CONFIGURATION_ENABLED = os.environ.get("MANAGED_CONFIGURATION_ENABLED", "false").lower() == "true"
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

ROBUSTA_API_ENDPOINT = os.environ.get("ROBUSTA_API_ENDPOINT", "https://api.robusta.dev")
ROBUSTA_TELEMETRY_ENDPOINT = os.environ.get("ROBUSTA_TELEMETRY_ENDPOINT", "https://api.robusta.dev/telemetry")
ENABLE_TELEMETRY = os.environ.get("ENABLE_TELEMETRY", "true").lower() == "true"
SEND_ADDITIONAL_TELEMETRY = os.environ.get("SEND_ADDITIONAL_TELEMETRY", "false").lower() == "true"
SENTRY_DSN = os.environ.get("SENTRY_DSN", "")
RELEASE_NAME = os.environ.get("RELEASE_NAME", "robusta")

RUNNER_SERVICE_ACCOUNT = os.environ.get("RUNNER_SERVICE_ACCOUNT", f"{RELEASE_NAME}-runner-service-account")

TELEMETRY_PERIODIC_SEC = int(os.environ.get("TELEMETRY_PERIODIC_SEC", 60 * 60 * 24))  # 24H

SLACK_REQUEST_TIMEOUT = int(os.environ.get("SLACK_REQUEST_TIMEOUT", 90))
SLACK_TABLE_COLUMNS_LIMIT = int(os.environ.get("SLACK_TABLE_COLUMNS_LIMIT", 3))
DISCORD_TABLE_COLUMNS_LIMIT = int(os.environ.get("DISCORD_TABLE_COLUMNS_LIMIT", 4))
RSA_KEYS_PATH = os.environ.get("RSA_KEYS_PATH", "/etc/robusta/auth")

# default of 120 seconds was chosen, because we saw some disconnections after 6 minutes. We needed a lower interval
WEBSOCKET_PING_INTERVAL = int(os.environ.get("WEBSOCKET_PING_INTERVAL", 120))
# Timeout for the ping response, before killing the connection. Must be smaller than the interval
WEBSOCKET_PING_TIMEOUT = int(os.environ.get("WEBSOCKET_PING_TIMEOUT", 30))

TRACE_INCOMING_REQUESTS = load_bool("TRACE_INCOMING_REQUESTS", False)
TRACE_INCOMING_ALERTS = load_bool("TRACE_INCOMING_ALERTS", False)

SERVICE_CACHE_TTL_SEC = int(os.environ.get("SERVICE_CACHE_TTL_SEC", 900))
SERVICE_CACHE_MAX_SIZE = int(os.environ.get("SERVICE_CACHE_MAX_SIZE", 1000))

PORT = int(os.environ.get("PORT", 5000))  # PORT

# additional certificate to verify, base64 encoded.
ADDITIONAL_CERTIFICATE: str = os.environ.get("CERTIFICATE", "")

DISCOVERY_MAX_BATCHES = int(os.environ.get("DISCOVERY_MAX_BATCHES", 25))
DISCOVERY_BATCH_SIZE = int(os.environ.get("DISCOVERY_BATCH_SIZE", 30000))
DISCOVERY_POD_OWNED_PODS = load_bool("DISCOVERY_POD_OWNED_PODS", False)

DISABLE_HELM_MONITORING = load_bool("DISABLE_HELM_MONITORING", False)

PROMETHEUS_ERROR_LOG_PERIOD_SEC = int(os.environ.get("DISCOVERY_MAX_BATCHES", 14400))

RRM_PERIOD_SEC = int(os.environ.get("RRM_PERIOD_SEC", 90))

MAX_ALLOWED_RULES_PER_CRD_ALERT = int(os.environ.get("MAX_ALLOWED_RULES_PER_CRD_ALERT", 600))

IMAGE_REGISTRY = os.environ.get("IMAGE_REGISTRY", "robustadev")

FIO_IMAGE = os.environ.get("FIO_IMAGE", "robusta-fio-benchmark:1.0")
DISK_TOOLS_IMAGE = os.environ.get("DISK_TOOLS_IMAGE", "disk-tools:1.6")

CLUSTER_DOMAIN = os.environ.get("CLUSTER_DOMAIN", "cluster.local")

IS_OPENSHIFT = load_bool("IS_OPENSHIFT", False)
OPENSHIFT_GROUPS = load_bool("OPENSHIFT_GROUPS", False)

ENABLE_GRAPH_BLOCK = load_bool("ENABLE_GRAPH_BLOCK", True)

RUN_AS_SUBPROCESS = load_bool("RUN_AS_SUBPROCESS", True)

ARGO_ROLLOUTS = load_bool("ARGO_ROLLOUTS", False)
# lowered case k8s kinds in a json array string. "[\"configmap\", \"secret\"]"
RESOURCE_YAML_BLOCK_LIST = json.loads(os.environ.get("RESOURCE_YAML_BLOCK_LIST", "[]"))

NAMESPACE_DATA_TTL = int(os.environ.get("NAMESPACE_DATA_TTL", 30 * 60))  # in seconds

PROCESSED_ALERTS_CACHE_TTL = int(os.environ.get("PROCESSED_ALERT_CACHE_TTL", 2 * 3600))
PROCESSED_ALERTS_CACHE_MAX_SIZE = int(os.environ.get("PROCESSED_ALERTS_CACHE_MAX_SIZE", 100_000))

POD_WAIT_RETRIES = int(os.environ.get("POD_WAIT_RETRIES", 10))
POD_WAIT_RETRIES_SECONDS = int(os.environ.get("POD_WAIT_RETRIES_SECONDS", 5))

HOLMES_ENABLED = load_bool("HOLMES_ENABLED", False)
HOLMES_ASK_SLACK_BUTTON_ENABLED = load_bool("HOLMES_ASK_SLACK_BUTTON_ENABLED", True)

# simple calculated values (not direct environment vars)
SENTRY_ENABLED = SEND_ADDITIONAL_TELEMETRY and SENTRY_DSN

# enable custom CRDs supported by robusta "["StrimziPodSet", "Cluster"]"
CUSTOM_CRD = json.loads(os.environ.get("CUSTOM_CRD", "[]"))
