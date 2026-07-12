import importlib
import json
import logging
from io import StringIO


def _reload_log_init(monkeypatch, json_enabled: bool):
    """Reload env_vars + log_init so ENABLE_JSON_LOGS_FORMAT is re-read from env."""
    monkeypatch.setenv("ENABLE_JSON_LOGS_FORMAT", "true" if json_enabled else "false")

    import robusta.core.model.env_vars as env_vars

    importlib.reload(env_vars)

    import robusta.runner.log_init as log_init

    importlib.reload(log_init)
    return log_init


def _capture_root_output() -> StringIO:
    """Attach a StringIO stream handler to the root logger and return the buffer."""
    buffer = StringIO()
    handler = logging.StreamHandler(buffer)
    handler.setFormatter(logging.getLogger().handlers[0].formatter)
    logging.getLogger().addHandler(handler)
    return buffer


def test_json_logging_emits_valid_json(monkeypatch):
    log_init = _reload_log_init(monkeypatch, json_enabled=True)
    log_init.init_logging()

    buffer = _capture_root_output()
    logging.getLogger().info("hello json")

    line = buffer.getvalue().strip().splitlines()[-1]
    payload = json.loads(line)
    assert payload["message"] == "hello json"
    # levelname is renamed to severity to match the other Robusta services.
    assert payload["severity"] == "INFO"


def test_plain_logging_is_not_json(monkeypatch):
    log_init = _reload_log_init(monkeypatch, json_enabled=False)
    log_init.init_logging()

    buffer = _capture_root_output()
    logging.getLogger().info("hello text")

    line = buffer.getvalue().strip().splitlines()[-1]
    assert "hello text" in line
    try:
        json.loads(line)
        is_json = True
    except json.JSONDecodeError:
        is_json = False
    assert not is_json
