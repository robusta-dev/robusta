import base64
import hashlib
import hmac
import logging
import time
from typing import Optional, Dict, Any
from uuid import UUID
import websocket
import json
import os
from threading import Thread
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey

from ..core.playbooks.playbook_utils import to_safe_str
from ..core.playbooks.playbooks_event_handler import PlaybooksEventHandler
from ..core.model.env_vars import INCOMING_REQUEST_TIME_WINDOW_SECONDS, RUNNER_VERSION
from ..core.reporting.action_requests import (
    ExternalActionRequest,
    ActionRequestBody,
    sign_action_request, PartialAuth,
)
from ..utils.auth_provider import AuthProvider

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
        self.auth_provider = AuthProvider()

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

    @classmethod
    def __sync_response(cls, status_code: int, request_id: str, data) -> Dict:
        return {
            "action": "response",
            "request_id": request_id,
            "status_code": status_code,
            "data": data
        }

    def __exec_external_request(
        self, action_request: ExternalActionRequest, validate_timestamp: bool
    ):
        logging.info(f"Callback `{action_request.body.action_name}` {to_safe_str(action_request.body.action_params)}")
        sync_response = action_request.request_id != ""  # if request_id is set, we need to write back the response
        if not self.__validate_request(action_request, validate_timestamp):
            req_json = action_request.json(exclude={"body"})
            body_json = action_request.body.json(exclude={"action_params"})  # action params already printed above
            logging.error(f"Failed to validate action request {req_json} {body_json}")
            if sync_response:
                self.ws.send(data=json.dumps(self.__sync_response(401, action_request.request_id, "")))
            return

        response = self.event_handler.run_external_action(
            action_request.body.action_name,
            action_request.body.action_params,
            action_request.body.sinks,
            sync_response,
            action_request.no_sinks,
        )

        if sync_response:
            http_code = 200 if response.get("success") else 500
            self.ws.send(data=json.dumps(self.__sync_response(http_code, action_request.request_id, response)))

    def on_message(self, ws, message):
        # TODO: use typed pydantic classes here?
        incoming_event = json.loads(message)
        actions = incoming_event.get("actions", None)
        if actions:  # this is slack callback format
            # slack callbacks have a list of 'actions'. Within each action there a 'value' field,
            # which container the actual action details we need to run.
            # This wrapper format is part of the slack API, and cannot be changed by us.
            for action in actions:
                raw_action = action.get("value", None)
                try:
                    self.__exec_external_request(
                        ExternalActionRequest.parse_raw(raw_action), False
                    )
                except Exception:
                    logging.error(
                        f"Failed to run incoming event {ActionRequestReceiver._stringify_incoming_event(raw_action)}",
                        exc_info=True
                    )
        else:  # assume it's ActionRequest format
            try:
                self.__exec_external_request(
                    ExternalActionRequest(**incoming_event), True
                )
            except Exception:
                logging.error(
                    f"Failed to run incoming event {ActionRequestReceiver._stringify_incoming_event(incoming_event)}",
                    exc_info=True
                )

    @staticmethod
    def _stringify_incoming_event(incoming_event) -> str:
        """Stringify incoming request masking action params in case it contains secrets"""
        if isinstance(incoming_event, str):  # slack format, stringified json
            try:
                event_dict = json.loads(incoming_event)
            except Exception:
                logging.error("Failed to parse raw incoming event", exc_info=True)
                return "parse error"
        elif isinstance(incoming_event, dict):
            event_dict = incoming_event
        else:
            return f"Unknown incoming_event type {type(incoming_event)}"
        body = event_dict.pop("body", {})
        action_params = body.pop("action_params", {})
        return f"{event_dict} {body} {to_safe_str(action_params)}"

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

    def __validate_request(self, action_request: ExternalActionRequest, validate_timestamp: bool) -> bool:
        """
            Two auth protocols are supported:
            1. signature - Signing the body using the signing_key should match the signature
            2. partial keys auth - using partial_auth_a and partial_auth_b
               Each partial auth should be decrypted using the private key (rsa private key).
               The content should have 2 items:
               - key
               - body hash
               The operation key_a XOR key_b should be equal to the signing_key

            If both protocols are present, we only check the signature
        """
        if validate_timestamp and (
            time.time() - action_request.body.timestamp
            > INCOMING_REQUEST_TIME_WINDOW_SECONDS
        ):
            logging.error(
                f"Rejecting incoming request because it's too old. Cannot verify request {action_request}"
            )
            return False

        signing_key = self.event_handler.get_global_config().get("signing_key")
        body = action_request.body
        if not signing_key:
            logging.error(f"Signing key not available. Cannot verify request {body}")
            return False

        # First auth protocol option, based on signature only
        signature = action_request.signature
        if signature:
            generated_signature = sign_action_request(body, signing_key)
            return hmac.compare_digest(generated_signature, signature)

        # Second auth protocol option, based on public key
        partial_auth_a = action_request.partial_auth_a
        partial_auth_b = action_request.partial_auth_b
        if not partial_auth_a or not partial_auth_b:
            logging.error(f"Insufficient authentication data. Cannot verify request {body}")
            return False

        private_key = self.auth_provider.get_private_rsa_key()
        if not private_key:
            logging.error(f"Private RSA key missing. Cannot validate request for {body}")
            return False

        a_valid, key_a = self.__extract_key_and_validate(partial_auth_a, private_key, body)
        b_valid, key_b = self.__extract_key_and_validate(partial_auth_b, private_key, body)

        if not a_valid or not b_valid:
            logging.error(f"Cloud not validate partial auth for {body}")
            return False

        try:
            signing_key_uuid = UUID(signing_key)
        except Exception:
            logging.error(f"Wrong signing key format. Cannot validate parital auth for {body}")
            return False

        if (key_a.int ^ key_b.int) != signing_key_uuid.int:
            logging.error(f"Partial auth keys combination mismatch for {body}")
            return False

        return True

    @classmethod
    def __extract_key_and_validate(
            cls,
            encrypted: str,
            private_key: RSAPrivateKey,
            body: ActionRequestBody
    ) -> (bool, Optional[UUID]):
        try:
            plain = private_key.decrypt(
                base64.b64decode(encrypted.encode("utf-8")),
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            auth = PartialAuth(**json.loads(plain.decode("utf-8")))
            body_string = body.json(exclude_none=True, sort_keys=True, separators=(',', ':')).encode("utf-8")
            body_hash = f"v0={hashlib.sha256(body_string).hexdigest()}"
            return hmac.compare_digest(body_hash, auth.hash), auth.key
        except Exception:
            logging.error("Error validating partial auth data", exc_info=True)
            return False, None
