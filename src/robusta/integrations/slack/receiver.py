import websocket
import json
import os
import time
from threading import Thread

from ...core.model.env_vars import TARGET_ID
from ...core.reporting.callbacks import *

SLACK_WEBSOCKET_RELAY_ADDRESS = os.environ.get("SLACK_WEBSOCKET_RELAY_ADDRESS", "wss://relay.robusta.dev")
SLACK_RECEIVER_ENABLED = os.environ.get("SLACK_RECEIVER_ENABLED", "True")
SLACK_ENABLE_WEBSOCKET_TRACING = os.environ.get("SLACK_ENABLE_WEBSOCKET_TRACING", False)
SLACK_WEBSOCKET_RECONNECT_DELAY_SEC = os.environ.get(
    "SLACK_WEBSOCKET_RECONNECT_DELAY_SEC", 3
)


def run_report_callback(action, body):
    try:
        callback_request = PlaybookCallbackRequest.parse_raw(action["value"])
        func = callback_registry.lookup_callback(callback_request)
        channel = body["channel"]["name"]
        event = SinkCallbackEvent(
            source_channel_id=body["channel"]["id"],
            source_channel_name=channel,
            source_user_id=body["user"]["id"],
            source_message=body["message"]["text"],
            source_context=callback_request.context,
        )
        logging.info(f"got callback `{func}`")
        if func is None:
            logging.error(
                f"no callback found for action_id={action['action_id']} with value={action['value']}"
            )
            return
        func(event)
        context = json.loads(callback_request.context)
        sink_name = context["sink_name"]
        # TODO Can we solve this cyclic import better?
        from ...core.sinks.sink_manager import SinkManager

        SinkManager.get_sink_by_name(sink_name).write_finding(event.finding)
    except Exception as e:
        logging.error(f"Error running callback; action={action}; e={e}")


def start_slack_receiver():
    if SLACK_RECEIVER_ENABLED != "True":
        logging.info(
            "Slack outgoing messages only mode. Slack receiver not initialized"
        )
        return

    if SLACK_WEBSOCKET_RELAY_ADDRESS == "":
        logging.warning("Slack relay adress empty. Not initializing slack relay")
        return

    websocket.enableTrace(SLACK_ENABLE_WEBSOCKET_TRACING)
    receiver_thread = Thread(target=run_forever)
    receiver_thread.start()


def run_forever():
    logging.info("starting slack relay receiver")
    while True:
        ws = websocket.WebSocketApp(
            SLACK_WEBSOCKET_RELAY_ADDRESS,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
        )
        ws.run_forever()
        logging.info("slack relay websocket closed")
        time.sleep(SLACK_WEBSOCKET_RECONNECT_DELAY_SEC)


def on_message(ws, message):
    # TODO: use typed pydantic classes here?
    logging.debug(f"received slack message {message}")
    slack_event = json.loads(message)
    actions = slack_event["actions"]
    for action in actions:
        run_report_callback(action, slack_event)


def on_error(ws, error):
    logging.info(f"slack relay websocket error: {error}")


def on_open(ws):
    logging.info(f"connecting to server as {TARGET_ID}")
    ws.send(json.dumps({"action": "auth", "key": "dummy key", "target_id": TARGET_ID}))
