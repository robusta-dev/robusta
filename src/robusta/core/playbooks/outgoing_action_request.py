import logging

import requests

from ..model.env_vars import RELAY_EXTERNAL_ACTIONS_URL
from ...integrations.action_requests import (
    ActionRequest,
    ActionRequestBody,
    sign_action_request,
)


class OutgoingActionRequest:
    @staticmethod
    def send(body: ActionRequestBody, signing_key: str):
        signature = sign_action_request(body, signing_key)
        action_request = ActionRequest(
            signature=signature,
            body=body,
        )

        resp = requests.post(RELAY_EXTERNAL_ACTIONS_URL, json=action_request.dict())
        if resp.status_code != 200:
            logging.error(
                f"Failed to send external action request {resp.status_code} {resp.reason}"
            )
