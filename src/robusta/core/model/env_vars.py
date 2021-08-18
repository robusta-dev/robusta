import os
import uuid

TARGET_ID = os.environ.get("RELAY_TARGET_ID", str(uuid.uuid4()))
DISCOVERY_PERIOD_SEC = int(os.environ.get("DISCOVERY_PERIOD_SEC", 90))
SUPABASE_LOGIN_RATE_LIMIT_SEC = int(
    os.environ.get("SUPABASE_LOGIN_RATE_LIMIT_SEC", 900)
)
GRAFANA_RENDERER_URL = os.environ.get(
    "GRAFANA_RENDERER_URL", "http://127.0.0.1:8281/render"
)
