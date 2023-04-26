import logging
import time
from typing import List

import requests

from robusta.core.model.env_vars import PORT
from robusta.core.model.helm_release import HelmRelease


class WebApi:
    @staticmethod
    def run_manual_action(action_name: str, action_params=None, sinks=None, retries=1, timeout_delay=1):
        if sinks is None:
            sinks = []
        if action_params is None:
            action_params = {"annotation": None}
        status_code = -1

        manual_action_url = f"http://127.0.0.1:{PORT}/api/trigger"
        data = {
            "action_name": action_name,
            "action_params": action_params,
            "sinks": sinks,
        }
        for _ in range(retries):
            try:
                response = requests.post(manual_action_url, json=data)
                status_code = response.status_code
                if status_code == 200:
                    return status_code

                logging.error(
                    f"Failed to run manual action \naction_name:{action_name}\n"
                    f"Reason: {response.reason}\nStatus Code{status_code}"
                )
            except Exception:
                logging.error("Error sending manual action request", exc_info=True)

            time.sleep(timeout_delay)

        return status_code

    @staticmethod
    def send_helm_release_events(release_data: List[HelmRelease], retries=1, timeout_delay=1):
        status_code = -1

        manual_action_url = f"http://127.0.0.1:{PORT}/api/helm-releases"
        data = {
            "version": "1",
            "data": release_data,
        }
        for _ in range(retries):
            try:
                response = requests.post(manual_action_url, json=data)
                status_code = response.status_code
                if status_code == 200:
                    return status_code

                logging.error(
                    f"Failed to send helm release events\n"
                    f"Reason: {response.reason}\nStatus Code{status_code}"
                )
            except Exception:
                logging.error("Error sending helm release events request", exc_info=True)

            time.sleep(timeout_delay)

        return status_code
