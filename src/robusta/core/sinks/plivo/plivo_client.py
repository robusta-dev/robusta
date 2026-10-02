import logging

import requests

PLIVO_API_BASE = "https://api.plivo.com/v1/Account"


class PlivoClient:
    def __init__(self, auth_id: str, auth_token: str):
        self.auth_id = str(auth_id)
        self.auth_token = str(auth_token)

    def send_message(self, src: str, dst: str, text: str):
        url = f"{PLIVO_API_BASE}/{self.auth_id}/Message/"
        payload = {"src": src, "dst": dst, "text": text, "type": "sms"}

        try:
            response = requests.post(
                url, json=payload, auth=(self.auth_id, self.auth_token), timeout=(5, 15)
            )
            if not response.ok:
                logging.error(
                    f"Failed to send Plivo SMS to {dst}: {response.status_code} {response.reason} {response.text}"
                )
        except Exception as e:
            logging.error(f"Error sending Plivo SMS to {dst}: {e}", exc_info=True)
