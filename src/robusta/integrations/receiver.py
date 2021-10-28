import logging
import websocket
import json
import os
import time
from threading import Thread

from ..core.model.events import ExecutionBaseEvent
from ..model.playbook_action import PlaybookAction
from ..core.playbooks.playbooks_event_handler import PlaybooksEventHandler
from ..core.model.env_vars import TARGET_ID
from ..core.reporting.callbacks import *

WEBSOCKET_RELAY_ADDRESS = os.environ.get(
    "WEBSOCKET_RELAY_ADDRESS", "wss://relay.robusta.dev"
)
INCOMING_RECEIVER_ENABLED = os.environ.get("INCOMING_RECEIVER_ENABLED", "True")
RECEIVER_ENABLE_WEBSOCKET_TRACING = "True" == os.environ.get(
    "RECEIVER_ENABLE_WEBSOCKET_TRACING"
)
INCOMING_WEBSOCKET_RECONNECT_DELAY_SEC = int(
    os.environ.get("INCOMING_WEBSOCKET_RECONNECT_DELAY_SEC", 3)
)


class ActionRequestReceiver:
    def __init__(self, event_handler: PlaybooksEventHandler):
        self.event_handler = event_handler
        self.active = True
        self.start_incoming_receiver()

    def run_report_callback(self, action, body):
        try:
            incoming_request = IncomingRequest.parse_raw(action["value"])
            if isinstance(incoming_request.incoming_request, ExternalActionRequest):
                self.__run_external_action_request(
                    incoming_request.incoming_request, body
                )
            else:
                logging.error(
                    f"Unknown incoming request type {incoming_request.incoming_request}"
                )
        except Exception as e:
            logging.error(f"Error running callback; action={action}; e={e}")

    def __run_external_action_request(
        self, callback_request: ExternalActionRequest, body
    ):
        execution_event = ExecutionBaseEvent(
            named_sinks=callback_request.sinks,
        )
        logging.info(
            f"got callback `{callback_request.action_name}` {callback_request.action_params}"
        )
        action = PlaybookAction(
            action_name=callback_request.action_name,
            action_params=callback_request.action_params,
        )
        self.event_handler.run_actions(execution_event, [action])

    def start_incoming_receiver(self):
        if INCOMING_RECEIVER_ENABLED != "True":
            logging.info(
                "outgoing messages only mode. Incoming event receiver not initialized"
            )
            return

        if WEBSOCKET_RELAY_ADDRESS == "":
            logging.warning("relay adress empty. Not initializing relay")
            return

        websocket.enableTrace(RECEIVER_ENABLE_WEBSOCKET_TRACING)
        receiver_thread = Thread(target=self.run_forever)
        receiver_thread.start()

    def run_forever(self):
        logging.info("starting relay receiver")
        while self.active:
            ws = websocket.WebSocketApp(
                WEBSOCKET_RELAY_ADDRESS,
                on_open=self.on_open,
                on_message=self.on_message,
                on_error=self.on_error,
            )
            ws.run_forever()
            logging.info("relay websocket closed")
            time.sleep(INCOMING_WEBSOCKET_RECONNECT_DELAY_SEC)

    def stop(self):
        logging.info(f"Stopping incoming receiver")
        self.active = False

    def on_message(self, ws, message):
        # TODO: use typed pydantic classes here?
        logging.debug(f"received incoming message {message}")
        incoming_event = json.loads(message)
        actions = incoming_event["actions"]
        for action in actions:
            self.run_report_callback(action, incoming_event)

    def on_error(self, ws, error):
        logging.info(f"Relay websocket error: {error}")

    def on_open(self, ws):
        logging.info(f"connecting to server as {TARGET_ID}")
        ws.send(
            json.dumps({"action": "auth", "key": "dummy key", "target_id": TARGET_ID})
        )
