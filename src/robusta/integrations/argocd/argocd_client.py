import logging

import requests


class ArgoCDClient:
    SYNC_APP_PATTERN = "{0}/api/v1/applications/{1}/sync"

    def __init__(self, url: str, token: str, verify_cert: bool = True):
        self.url = url
        self.token = token
        self.verify_cert = verify_cert
        self.headers = {
            "Authorization": f"Bearer {self.token}",
        }

    def sync_application(self, application_name: str) -> bool:
        sync_url = self.SYNC_APP_PATTERN.format(self.url, application_name)

        argo_response = requests.post(
            sync_url, headers=self.headers, verify=self.verify_cert
        )
        if argo_response.status_code != 200:
            logging.error(
                f"Failed to sync application {application_name} on argo {self.url} {argo_response.reason}"
            )
            return False

        return True
