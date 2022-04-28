import os
import uuid
import pytz

PLAYBOOKS_ROOT = os.environ.get("PLAYBOOKS_ROOT", "/etc/robusta/playbooks/")
# should be the same as the one in out Dockerfile
DEFAULT_PLAYBOOKS_ROOT = os.environ.get("DEFAULT_PLAYBOOKS_ROOT", os.path.join(PLAYBOOKS_ROOT, "defaults"))
CUSTOM_PLAYBOOKS_ROOT = os.path.join(PLAYBOOKS_ROOT, "storage")

PLAYBOOKS_CONFIG_FILE_PATH = os.environ.get("PLAYBOOKS_CONFIG_FILE_PATH")

INSTALLATION_NAMESPACE = os.environ.get("INSTALLATION_NAMESPACE", "robusta")
DISCOVERY_PERIOD_SEC = int(os.environ.get("DISCOVERY_PERIOD_SEC", 90))
PERIODIC_LONG_SEC = int(os.environ.get("PERIODIC_LONG_SEC", 60 * 60 * 3))
SUPABASE_LOGIN_RATE_LIMIT_SEC = int(
    os.environ.get("SUPABASE_LOGIN_RATE_LIMIT_SEC", 900)
)
GRAFANA_RENDERER_URL = os.environ.get(
    "GRAFANA_RENDERER_URL", "http://127.0.0.1:8281/render"
)
SERVICE_UPDATES_CACHE_TTL_SEC = os.environ.get("SERVICE_UPDATES_CACHE_TTL_SEC", 120)
INTERNAL_PLAYBOOKS_ROOT = os.environ.get(
    "INTERNAL_PLAYBOOKS_ROOT", "/app/src/robusta/core/playbooks/internal"
)
DEFAULT_TIMEZONE = pytz.timezone(os.environ.get("DEFAULT_TIMEZONE", "UTC"))
NUM_EVENT_THREADS = int(os.environ.get("NUM_EVENT_THREADS", 10))
INCOMING_EVENTS_QUEUE_MAX_SIZE = int(
    os.environ.get("INCOMING_EVENTS_QUEUE_MAX_SIZE", 500)
)

FLOAT_PRECISION_LIMIT = int(os.environ.get("FLOAT_PRECISION_LIMIT", 11))

PROMETHEUS_REQUEST_TIMEOUT_SECONDS = float(
    os.environ.get("PROMETHEUS_REQUEST_TIMEOUT_SECONDS", 90.0)
)
PROMETHEUS_ENABLED = os.environ.get("PROMETHEUS_ENABLED", "false").lower() == "true"

INCOMING_REQUEST_TIME_WINDOW_SECONDS = int(
    os.environ.get("INCOMING_REQUEST_TIME_WINDOW_SECONDS", 3600)
)

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
TELEMETRY_PERIODIC_SEC = int(os.environ.get("TELEMETRY_PERIODIC_SEC", 60 * 60 * 24)) # 24H

SLACK_TABLE_COLUMNS_LIMIT = int(os.environ.get("SLACK_TABLE_COLUMNS_LIMIT", 4))
RSA_KEYS_PATH = os.environ.get("RSA_KEYS_PATH", "/etc/robusta/auth")
