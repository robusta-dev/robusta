import logging
import time

import requests


class WebApi:

    @staticmethod
    def run_manual_action(action_name: str, params, sinks, retries=1, timeout_delay=1):
        MANUAL_ACTION_URL = "http://127.0.0.1:5000/api/trigger"
        data = { "action_name": action_name, "action_params": params, "sinks": sinks }
        for _ in range(retries):
            response = requests.post(
                MANUAL_ACTION_URL,
                json=data
            )

            if response.status_code == 200:
                return response.status_code

            logging.error(
                f"Failed to run manual action \naction_name:{action_name}\n"
                f"params:{params}\nReason: {response.reason}\nStatus Code{response.status_code}"
            )
            time.sleep(timeout_delay)

        return response.status_code
