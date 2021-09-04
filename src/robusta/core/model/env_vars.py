import os
import uuid
import pytz

INSTALLATION_NAMESPACE = os.environ.get("INSTALLATION_NAMESPACE", "robusta")
TARGET_ID = os.environ.get("RELAY_TARGET_ID", str(uuid.uuid4()))
DISCOVERY_PERIOD_SEC = int(os.environ.get("DISCOVERY_PERIOD_SEC", 90))
SUPABASE_LOGIN_RATE_LIMIT_SEC = int(
    os.environ.get("SUPABASE_LOGIN_RATE_LIMIT_SEC", 900)
)
GRAFANA_RENDERER_URL = os.environ.get(
    "GRAFANA_RENDERER_URL", "http://127.0.0.1:8281/render"
)
SERVICE_UPDATES_CACHE_TTL_SEC = os.environ.get("SERVICE_UPDATES_CACHE_TTL_SEC", 120)
INTERNAL_PLAYBOOKS_ROOT = os.environ.get(
    "INTERNAL_PLAYBOOKS_ROOT", "/app/robusta/core/playbooks/internal"
)
DEFAULT_TIMEZONE = pytz.timezone(os.environ.get("DEFAULT_TIMEZONE", "UTC"))
NUM_EVENT_THREADS = int(os.environ.get("NUM_EVENT_THREADS", 20))
