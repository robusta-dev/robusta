import hmac
import logging
import time
import traceback
import websocket
import json
import os
from threading import Thread
from pydantic import BaseModel

from ..core.playbooks.playbooks_event_handler import PlaybooksEventHandler
from ..core.model.env_vars import INCOMING_REQUEST_TIME_WINDOW_SECONDS, RUNNER_VERSION
from robusta.core.reporting.action_requests import (
    ExternalActionRequest,
    ActionRequestBody,
    sign_action_request,
)

WEBSOCKET_RELAY_ADDRESS = os.environ.get(
    "WEBSOCKET_RELAY_ADDRESS", "wss://relay.robusta.dev"
)
CLOUD_ROUTING = json.loads(os.environ.get("CLOUD_ROUTING", "True").lower())
RECEIVER_ENABLE_WEBSOCKET_TRACING = json.loads(
    os.environ.get("RECEIVER_ENABLE_WEBSOCKET_TRACING", "False").lower()
)
INCOMING_WEBSOCKET_RECONNECT_DELAY_SEC = int(
    os.environ.get("INCOMING_WEBSOCKET_RECONNECT_DELAY_SEC", 3)
)


class ActionRequestReceiver:
    def __init__(self, event_handler: PlaybooksEventHandler):
        self.event_handler = event_handler
        self.active = True
        self.account_id = self.event_handler.get_global_config().get("account_id")
        self.cluster_name = self.event_handler.get_global_config().get("cluster_name")

        self.ws = websocket.WebSocketApp(
            WEBSOCKET_RELAY_ADDRESS,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
        )

        if not self.account_id or not self.cluster_name:
            logging.error(
                f"Action receiver cannot start. "
                f"Missing required account_id {self.account_id} cluster_name {self.cluster_name}"
            )
            return

        self.start_receiver()

    def start_receiver(self):
        if not CLOUD_ROUTING:
            logging.info(
                "outgoing messages only mode. Incoming event receiver not initialized"
            )
            return

        if WEBSOCKET_RELAY_ADDRESS == "":
            logging.warning("relay address empty. Not initializing relay")
            return

        websocket.enableTrace(RECEIVER_ENABLE_WEBSOCKET_TRACING)
        receiver_thread = Thread(target=self.run_forever)
        receiver_thread.start()

    def __run_external_action_request(self, request: ActionRequestBody):
        logging.info(f"got callback `{request.action_name}` {request.action_params}")
        self.event_handler.run_external_action(
            request.action_name,
            request.action_params,
            request.sinks,
        )

    def run_forever(self):
        logging.info("starting relay receiver")
        while self.active:
            self.ws.run_forever()
            logging.info("relay websocket closed")
            time.sleep(INCOMING_WEBSOCKET_RECONNECT_DELAY_SEC)

    def stop(self):
        logging.info(f"Stopping incoming receiver")
        self.active = False
        self.ws.close()

    def __exec_external_request(
        self, action_request: ExternalActionRequest, validate_timestamp: bool
    ):
        if validate_timestamp and (
            time.time() - action_request.body.timestamp
            > INCOMING_REQUEST_TIME_WINDOW_SECONDS
        ):
            logging.error(
                f"Rejecting incoming request because it's too old. Cannot verify request {action_request}"
            )
            return

        if not self.__validate_request(action_request.body, action_request.signature):
            logging.error(f"Failed to validate action request {action_request}")
            return

        self.__run_external_action_request(action_request.body)

    def on_message(self, ws, message):
        # TODO: use typed pydantic classes here?
        logging.debug(f"received incoming message {message}")
        incoming_event = json.loads(message)
        actions = incoming_event.get("actions", None)
        if actions:  # this is slack callback format
            # slack callbacks have a list of 'actions'. Within each action there a 'value' field,
            # which container the actual action details we need to run.
            # This wrapper format is part of the slack API, and cannot be changed by us.
            for action in actions:
                try:
                    self.__exec_external_request(
                        ExternalActionRequest.parse_raw(action["value"]), False
                    )
                except Exception:
                    logging.error(
                        f"Failed to run incoming event {incoming_event}", exc_info=True
                    )
        else:  # assume it's ActionRequest format
            try:
                self.__exec_external_request(
                    ExternalActionRequest(**incoming_event), True
                )
            except Exception:
                logging.error(
                    f"Failed to run incoming event {incoming_event}", exc_info=True
                )

    def on_error(self, ws, error):
        logging.info(f"Relay websocket error: {error}")

    def on_open(self, ws):
        account_id = self.event_handler.get_global_config().get("account_id")
        cluster_name = self.event_handler.get_global_config().get("cluster_name")
        open_payload = {
            "action": "auth",
            "account_id": account_id,
            "cluster_name": cluster_name,
            "version": RUNNER_VERSION,
        }
        logging.info(
            f"connecting to server as account_id={account_id}; cluster_name={cluster_name}"
        )
        ws.send(json.dumps(open_payload))

    def __validate_request(self, body: BaseModel, signature: str) -> bool:
        signing_key = self.event_handler.get_global_config().get("signing_key")
        if not signing_key:
            logging.error(f"Signing key not available. Cannot verify request {body}")
            return False

        generated_signature = sign_action_request(body, signing_key)
        return hmac.compare_digest(generated_signature, signature)
