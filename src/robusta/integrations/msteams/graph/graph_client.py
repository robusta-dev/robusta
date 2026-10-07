import logging
import threading
import time
from typing import Optional
from urllib.parse import quote, unquote

import requests

DEFAULT_AUTHORITY_HOST = "https://login.microsoftonline.com"
DEFAULT_GRAPH_ENDPOINT = "https://graph.microsoft.com"
REQUEST_TIMEOUT_SEC = 30
# refresh the access token a bit before it expires, so a message is never sent with an expiring token
TOKEN_EXPIRY_MARGIN_SEC = 300
# after a failed sign-in, don't retry on every alert: repeated bad passwords trigger Entra ID smart lockout
SIGN_IN_FAILURE_BACKOFF_SEC = 300


class MsTeamsGraphError(Exception):
    pass


class MsTeamsGraphClient:
    """Posts Teams channel messages via the Microsoft Graph API.

    Graph only supports posting channel messages with delegated permissions (application permissions are
    limited to message migration), so the token is acquired on behalf of a service user with the
    Resource Owner Password Credentials (ROPC) flow. The user must be a member of every target team,
    and must not require interactive MFA.
    """

    def __init__(
        self,
        tenant_id: str,
        client_id: str,
        username: str,
        password: str,
        client_secret: Optional[str] = None,
        scope: Optional[str] = None,
        authority_host: str = DEFAULT_AUTHORITY_HOST,
        graph_endpoint: str = DEFAULT_GRAPH_ENDPOINT,
    ):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.username = username
        self.password = password
        self.client_secret = client_secret
        self.authority_host = authority_host.rstrip("/")
        self.graph_endpoint = graph_endpoint.rstrip("/")
        self.scope = scope or f"{self.graph_endpoint}/.default"

        self._lock = threading.Lock()
        self._access_token: Optional[str] = None
        self._expires_at: float = 0
        self._next_sign_in_attempt: float = 0

    def _get_access_token(self, force_refresh: bool = False) -> str:
        with self._lock:
            if not force_refresh and self._access_token and time.time() < self._expires_at - TOKEN_EXPIRY_MARGIN_SEC:
                return self._access_token
            if time.time() < self._next_sign_in_attempt:
                raise MsTeamsGraphError(
                    f"Skipping Graph sign-in for {self.username}, it failed recently. "
                    f"Retrying in {int(self._next_sign_in_attempt - time.time())}s"
                )

            data = {
                "grant_type": "password",
                "client_id": self.client_id,
                "username": self.username,
                "password": self.password,
                "scope": self.scope,
            }
            if self.client_secret:
                data["client_secret"] = self.client_secret

            response = requests.post(
                f"{self.authority_host}/{self.tenant_id}/oauth2/v2.0/token", data=data, timeout=REQUEST_TIMEOUT_SEC
            )
            if not response.ok:
                self._next_sign_in_attempt = time.time() + SIGN_IN_FAILURE_BACKOFF_SEC
                raise MsTeamsGraphError(
                    f"Failed to get a Graph access token for {self.username}: "
                    f"{response.status_code} {self.error_message(response)}"
                )

            body = response.json()
            self._access_token = body["access_token"]
            self._expires_at = time.time() + int(body.get("expires_in", 3600))
            return self._access_token

    def post_channel_message(self, team_id: str, channel_id: str, message: dict) -> requests.Response:
        # channel ids look like 19:abc@thread.tacv2, and are often copied URL-encoded from the Teams channel link
        url = (
            f"{self.graph_endpoint}/v1.0/teams/{quote(unquote(team_id), safe='')}"
            f"/channels/{quote(unquote(channel_id), safe='')}/messages"
        )
        response = self._post(url, message, force_refresh=False)
        if response.status_code == 401:
            response = self._post(url, message, force_refresh=True)
        return response

    def _post(self, url: str, message: dict, force_refresh: bool) -> requests.Response:
        headers = {"Authorization": f"Bearer {self._get_access_token(force_refresh)}"}
        return requests.post(url, json=message, headers=headers, timeout=REQUEST_TIMEOUT_SEC)

    @staticmethod
    def error_message(response: requests.Response) -> str:
        try:
            body = response.json()
        except ValueError:
            return response.text
        error = body.get("error")
        if isinstance(error, dict):  # Graph errors
            return error.get("message", response.text)
        if body.get("error_description"):  # Entra ID token errors
            return f"{error}: {body['error_description']}"
        logging.debug("unexpected Graph error body %s", body)
        return response.text

