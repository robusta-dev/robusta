import base64
import hashlib
import hmac
import json
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import nullcontext
from threading import Thread
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

import sentry_sdk
import websocket
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from pydantic import BaseModel, ValidationError, validator

from robusta.core.model.env_vars import (
    INCOMING_REQUEST_TIME_WINDOW_SECONDS,
    RUNNER_VERSION,
    SENTRY_ENABLED,
    WEBSOCKET_PING_INTERVAL,
    WEBSOCKET_PING_TIMEOUT,
)
from robusta.core.playbooks.playbook_utils import to_safe_str
from robusta.core.playbooks.playbooks_event_handler import PlaybooksEventHandler
from robusta.core.reporting.action_requests import (
    ActionRequestBody,
    ExternalActionRequest,
    PartialAuth,
    sign_action_request,
)
from robusta.utils.auth_provider import AuthProvider
from robusta.utils.error_codes import ErrorCodes

WEBSOCKET_RELAY_ADDRESS = os.environ.get("WEBSOCKET_RELAY_ADDRESS", "wss://relay.robusta.dev")
RECEIVER_ENABLE_WEBSOCKET_TRACING = json.loads(os.environ.get("RECEIVER_ENABLE_WEBSOCKET_TRACING", "False").lower())
INCOMING_WEBSOCKET_RECONNECT_DELAY_SEC = int(os.environ.get("INCOMING_WEBSOCKET_RECONNECT_DELAY_SEC", 3))
WEBSOCKET_THREADPOOL_SIZE = int(os.environ.get("WEBSOCKET_THREADPOOL_SIZE", 10))


class ValidationResponse(BaseModel):
    http_code: int = 200
    error_code: Optional[int] = None
    error_msg: Optional[str] = None


class SlackExternalActionRequest(ExternalActionRequest):
    # Optional Slack Params
    slack_username: Optional[str] = None
    slack_message: Optional[Any] = None


class SlackActionRequest(BaseModel):
    value: SlackExternalActionRequest

    @validator("value", pre=True, always=True)
    def validate_value(cls, v: str) -> dict:
        # Slack value is sent as a stringified json, so we need to parse it before validation
        return json.loads(v)


class SlackUserID(BaseModel):
    username: str
    name: str
    team_id: str


class SlackActionsMessage(BaseModel):
    actions: List[SlackActionRequest]
    user: Optional[SlackUserID]


class ActionRequestReceiver:
    def __init__(self, event_handler: PlaybooksEventHandler, robusta_sink: "RobustaSink"):
        self.event_handler = event_handler
        self.active = True
        self.account_id = robusta_sink.account_id
        self.cluster_name = robusta_sink.cluster_name
        self.auth_provider = AuthProvider()
        self.healthy = False
        self.robusta_sink = robusta_sink

        self.ws = websocket.WebSocketApp(
            WEBSOCKET_RELAY_ADDRESS,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
        )

        self._executor = ThreadPoolExecutor(max_workers=WEBSOCKET_THREADPOOL_SIZE)

        if not self.account_id or not self.cluster_name:
            logging.error(
                f"Action receiver cannot start. "
                f"Missing required account_id {self.account_id} cluster_name {self.cluster_name}"
            )
            return

        self.start_receiver()

    def start_receiver(self):
        if WEBSOCKET_RELAY_ADDRESS == "":
            logging.warning("relay address empty. Not initializing relay")
            return

        self.healthy = True
        websocket.enableTrace(RECEIVER_ENABLE_WEBSOCKET_TRACING)
        receiver_thread = Thread(target=self.run_forever)
        receiver_thread.start()

    def run_forever(self):
        logging.info("starting relay receiver")
        while self.active:
            self.ws.run_forever(
                ping_interval=WEBSOCKET_PING_INTERVAL,
                ping_payload="p",
                ping_timeout=WEBSOCKET_PING_TIMEOUT,
            )
            logging.info("relay websocket closed")
            time.sleep(INCOMING_WEBSOCKET_RECONNECT_DELAY_SEC)

    def stop(self):
        logging.info("Stopping incoming receiver")
        self.active = False
        self.ws.close()

    @classmethod
    def __sync_response(cls, status_code: int, request_id: str, data) -> Dict:
        return {"action": "response", "request_id": request_id, "status_code": status_code, "data": data}

    def __stream_response(self, request_id: str, data: str):
        self.ws.send(data=json.dumps({"action": "stream", "request_id": request_id, "data": data}))

    def __close_stream_response(self, request_id: str, data: str):
        self.ws.send(data=json.dumps({"action": "stream", "request_id": request_id, "data": data, "close": True}))

    def __exec_external_request(self, action_request: ExternalActionRequest, validate_timestamp: bool):
        logging.debug(f"Callback `{action_request.body.action_name}` {to_safe_str(action_request.body.action_params)}")
        sync_response = action_request.request_id != ""  # if request_id is set, we need to write back the response
        validation_response = self.__validate_request(action_request, validate_timestamp)
        if validation_response.http_code != 200:
            req_json = action_request.json(exclude={"body"})
            body_json = action_request.body.json(exclude={"action_params"})  # action params already printed above
            logging.error(f"Failed to validate action request {req_json} {body_json}")
            if sync_response:
                self.ws.send(
                    data=json.dumps(
                        self.__sync_response(
                            status_code=validation_response.http_code,
                            request_id=action_request.request_id,
                            data=validation_response.dict(exclude={"http_code"}),
                        )
                    )
                )
            return

        # add global slack values to callback
        if hasattr(action_request, 'slack_username'):
            action_request.body.action_params["slack_username"] = action_request.slack_username

        if hasattr(action_request, 'slack_message'):
            action_request.body.action_params["slack_message"] = action_request.slack_message

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

    def __exec_external_stream_request(self, action_request: ExternalActionRequest, validate_timestamp: bool):
        logging.debug(f"Callback `{action_request.body.action_name}` {to_safe_str(action_request.body.action_params)}")

        validation_response = self.__validate_request(action_request, validate_timestamp)
        if validation_response.http_code != 200:
            req_json = action_request.json(exclude={"body"})
            body_json = action_request.body.json(exclude={"action_params"})  # action params already printed above
            logging.error(f"Failed to validate action request {req_json} {body_json}")
            self.__close_stream_response(action_request.request_id, validation_response.dict(exclude={"http_code"}))
            return

        res = self.event_handler.run_external_stream_action(action_request.body.action_name,
                                                            action_request.body.action_params,
                                                            lambda data: self.__stream_response(request_id=action_request.request_id, data=data))
        res = "" if res.get("success") else f"event: error\ndata: {json.dumps(res)}\n\n"
        self.__close_stream_response(action_request.request_id, res)

    def _process_action(self, action: ExternalActionRequest, validate_timestamp: bool) -> None:
        self._executor.submit(self._process_action_sync, action, validate_timestamp)

    def _process_action_sync(self, action: ExternalActionRequest, validate_timestamp: bool) -> None:
        try:
            if SENTRY_ENABLED:
                ctx = sentry_sdk.start_transaction(op="manual_action", name=action.body.action_name)
                ctx.set_tag("account_id", action.body.account_id)
                ctx.set_tag("cluster_name", action.body.cluster_name)
                ctx.set_tag("action_params", action.body.action_params)
                ctx.set_tag("origin", action.body.origin)
            else:
                ctx = nullcontext()
            with ctx:
                if action.stream:
                    self.__exec_external_stream_request(action, validate_timestamp)
                else:
                    self.__exec_external_request(action, validate_timestamp)
        except Exception:
            logging.error(
                f"Failed to run incoming event {self._stringify_incoming_event(action.dict())}",
                exc_info=True,
            )

    @staticmethod
    def _parse_websocket_message(
        message: Union[str, bytes, bytearray]
    ) -> Union[SlackActionsMessage, ExternalActionRequest]:
        try:
            return ActionRequestReceiver._parse_slack_message(message)  # this is slack callback format
        except ValidationError:
            return ExternalActionRequest.parse_raw(message)

    @staticmethod
    def _parse_slack_message(message: Union[str, bytes, bytearray]) -> SlackActionsMessage:
        slack_actions_message = SlackActionsMessage.parse_raw(message)  # this is slack callback format
        json_slack_message = json.loads(message)
        for action in slack_actions_message.actions:
            action.value.slack_username = slack_actions_message.user.username
            action.value.slack_message = json_slack_message
        return slack_actions_message

    def on_message(self, ws: websocket.WebSocketApp, message: str) -> None:
        """Callback for incoming websocket message from relay.

        The message can be in one of two formats:
        1. ExternalActionRequest - just one plain action request
        2. SlackActionsMessage - has multiple grouped action requests
        """

        try:
            incoming_event = self._parse_websocket_message(message)
        except Exception:
            logging.error(f"Failed to parse incoming event {message}", exc_info=True)
            return

        if isinstance(incoming_event, SlackActionsMessage):
            # slack callbacks have a list of 'actions'. Within each action there a 'value' field,
            # which container the actual action details we need to run.
            # This wrapper format is part of the slack API, and cannot be changed by us.
            for slack_action_request in incoming_event.actions:
                self._process_action(slack_action_request.value, validate_timestamp=False)
        else:
            self._process_action(incoming_event, validate_timestamp=True)

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
        token = self.robusta_sink.dal.get_session_token()
        open_payload = {
            "action": "auth",
            "account_id": self.account_id,
            "cluster_name": self.cluster_name,
            "version": RUNNER_VERSION,
            "token": token,
        }
        logging.info(f"connecting to server as account_id={self.account_id}; cluster_name={self.cluster_name}")
        ws.send(json.dumps(open_payload))

    def __validate_request(self, action_request: ExternalActionRequest, validate_timestamp: bool) -> ValidationResponse:
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
        if validate_timestamp and (time.time() - action_request.body.timestamp > INCOMING_REQUEST_TIME_WINDOW_SECONDS):
            logging.error(f"Rejecting incoming request because it's too old. Cannot verify request {action_request}")
            return ValidationResponse(
                http_code=500, error_code=ErrorCodes.ILLEGAL_TIMESTAMP.value, error_msg="Illegal timestamp"
            )

        signing_key = self.event_handler.get_global_config().get("signing_key")
        if not signing_key:
            logging.error(f"Signing key not available. Cannot verify request {action_request.body}")
            return ValidationResponse(
                http_code=500, error_code=ErrorCodes.NO_SIGNING_KEY.value, error_msg="No signing key"
            )

        if action_request.signature:
            # First auth protocol option, based on signature only
            return self.validate_action_request_signature(action_request, signing_key)
        elif action_request.partial_auth_a or action_request.partial_auth_b:
            # Second auth protocol option, based on public key
            return self.validate_with_private_key(action_request, signing_key)
        else:  # Light action protocol option, authenticated in relay
            return self.validate_light_action(action_request)

    def validate_light_action(self, action_request: ExternalActionRequest) -> ValidationResponse:
        light_actions = self.event_handler.get_light_actions()
        if action_request.body.action_name not in light_actions:
            return ValidationResponse(
                http_code=500,
                error_code=ErrorCodes.UNAUTHORIZED_LIGHT_ACTION.value,
                error_msg="Unauthorized action requested",
            )
        return ValidationResponse()

    @staticmethod
    def validate_action_request_signature(
        action_request: ExternalActionRequest, signing_key: str
    ) -> ValidationResponse:
        generated_signature = sign_action_request(action_request.body, signing_key)
        if hmac.compare_digest(generated_signature, action_request.signature):
            return ValidationResponse()
        else:
            return ValidationResponse(
                http_code=500, error_code=ErrorCodes.SIGNATURE_MISMATCH.value, error_msg="Signature mismatch"
            )

    def validate_with_private_key(self, action_request: ExternalActionRequest, signing_key: str) -> ValidationResponse:
        body = action_request.body
        partial_auth_a = action_request.partial_auth_a
        partial_auth_b = action_request.partial_auth_b
        if not partial_auth_a or not partial_auth_b:
            logging.error(f"Insufficient authentication data. Cannot verify request {body}")
            return ValidationResponse(
                http_code=500, error_code=ErrorCodes.MISSING_AUTH_INPUT.value, error_msg="Missing auth input"
            )

        private_key = self.auth_provider.get_private_rsa_key()
        if not private_key:
            logging.error(f"Private RSA key missing. Cannot validate request for {body}")
            return ValidationResponse(
                http_code=500, error_code=ErrorCodes.MISSING_PRIVATE_KEY.value, error_msg="Missing private key"
            )

        a_valid, key_a = self.__extract_key_and_validate(partial_auth_a, private_key, body)
        b_valid, key_b = self.__extract_key_and_validate(partial_auth_b, private_key, body)

        if not a_valid or not b_valid:
            logging.error(f"Cloud not validate partial auth for {body}")
            return ValidationResponse(
                http_code=401, error_code=ErrorCodes.AUTH_VALIDATION_FAILED.value, error_msg="Auth validation failed"
            )

        try:
            signing_key_uuid = UUID(signing_key)
        except Exception:
            logging.error(f"Wrong signing key format. Cannot validate parital auth for {body}")
            return ValidationResponse(
                http_code=500, error_code=ErrorCodes.BAD_SIGNING_KEY.value, error_msg="Bad signing key"
            )

        if not hmac.compare_digest(str(key_a.int ^ key_b.int), str(signing_key_uuid.int)):
            logging.error(f"Partial auth keys combination mismatch for {body}")
            return ValidationResponse(
                http_code=401, error_code=ErrorCodes.KEY_VALIDATION_FAILED.value, error_msg="Key validation failed"
            )

        return ValidationResponse()

    @classmethod
    def __extract_key_and_validate(
        cls, encrypted: str, private_key: RSAPrivateKey, body: ActionRequestBody
    ) -> (bool, Optional[UUID]):
        try:
            plain = private_key.decrypt(
                base64.b64decode(encrypted.encode("utf-8")),
                padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None),
            )
            auth = PartialAuth(**json.loads(plain.decode("utf-8")))
            body_string = body.json(exclude_none=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
            body_hash = f"v0={hashlib.sha256(body_string).hexdigest()}"
            return hmac.compare_digest(body_hash, auth.hash), auth.key
        except Exception:
            logging.error("Error validating partial auth data", exc_info=True)
            return False, None
