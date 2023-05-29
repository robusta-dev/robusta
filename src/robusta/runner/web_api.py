import logging
import time
from typing import List
from urllib.error import HTTPError

import requests

from robusta.core.model.env_vars import PORT
from robusta.core.model.helm_release import HelmRelease


class WebApi:

    @staticmethod
    def __post(url: str, data: dict, retries=1, timeout_delay=1):
        response = None

        for _ in range(retries):
            try:
                response = requests.post(url, json=data)
                status_code = response.status_code
                if status_code == 200:
                    return response
                response.raise_for_status()
            except Exception as e:
                raise e

            time.sleep(timeout_delay)

        return response

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

        try:
            response = WebApi.__post(url=manual_action_url, data=data, retries=retries, timeout_delay=timeout_delay)
            status_code = response.status_code
        except HTTPError as e:
            status_code = e.status

            logging.error(
                f"Failed to run manual action \naction_name:{action_name}\n"
                f"Reason: {e.reason}\nStatus Code{status_code}"
            )
        except Exception:
            logging.error("Error sending manual action request", exc_info=True)

        return status_code

    @staticmethod
    def send_helm_release_events(release_data: List[HelmRelease], retries=1, timeout_delay=1):
        status_code = -1

        url = f"http://127.0.0.1:{PORT}/api/helm-releases"
        data = {
            "data": HelmRelease.list_to_dict(release_data),
        }

        try:
            response = WebApi.__post(url=url, data=data, retries=retries, timeout_delay=timeout_delay)
            status_code = response.status_code
        except HTTPError as e:
            status_code = e.status

            logging.error(
                f"Failed to send helm release events\n"
                f"Reason: {e.reason}\nStatus Code{status_code}"
            )
        except Exception:
            logging.error("Error sending helm release events request", exc_info=True)

        return status_code
