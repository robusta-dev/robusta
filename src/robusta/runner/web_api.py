import logging
import time

import requests


class WebApi:
    @staticmethod
    def run_manual_action(action_name: str, action_params=None, sinks=None, retries=1, timeout_delay=1):
        if sinks is None:
            sinks = []
        if action_params is None:
            action_params = {"annotation": None}
        status_code = -1

        manual_action_url = "http://127.0.0.1:5000/api/trigger"
        data = { "action_name": action_name, "action_params": action_params, "sinks": sinks }
        for _ in range(retries):
            try:
                response = requests.post(
                    manual_action_url,
                    json=data
                )
                status_code = response.status_code
                if status_code == 200:
                    return status_code

                logging.error(
                    f"Failed to run manual action \naction_name:{action_name}\n"
                    f"Reason: {response.reason}\nStatus Code{status_code}"
                )
                time.sleep(timeout_delay)
            except Exception as e:
                logging.error(f"Error sending manual action request {e}")
                time.sleep(timeout_delay)

        return status_code
