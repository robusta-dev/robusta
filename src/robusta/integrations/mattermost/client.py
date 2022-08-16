import logging
from http import HTTPStatus
from typing import Optional, List, Dict

from ..common.requests import process_request, HttpMethod
from ...core.model.env_vars import ROBUSTA_LOGO_URL

_SUPPORTED_SCHEMAS = ['http', 'https']
_API_PREFIX = "api/v4"


class MattermostClient:
    def __init__(
            self, url: str, token: str, token_id: str, channel_id: str, schema: Optional[str]
    ):
        """
        Set the Mattermost webhook url.
        """
        self.client_url = url.split(":")[-1].lstrip("/").rstrip("/")
        self.token = token
        self.token_id = token_id
        self.channel_id = channel_id
        schema = schema or "https"
        if schema not in _SUPPORTED_SCHEMAS:
            raise AttributeError(f"{schema} is not supported schema, should be one of following: {_SUPPORTED_SCHEMAS}")
        self.schema = schema
        self._init_setup()

    def _send_mattermost_request(self, url: str, method: HttpMethod, **kwargs):
        headers = kwargs.pop("headers", {})
        headers['Authorization'] = f"Bearer {self.token}"
        return process_request(url, method, headers=headers, **kwargs)

    def _get_full_mattermost_url(self, endpoint, *args):
        return "/".join([
            f"{self.schema}:",
            "",
            self.client_url,
            _API_PREFIX,
            endpoint,
            *args
        ])

    def get_token_owner_id(self):
        endpoint = "users/tokens"
        url = self._get_full_mattermost_url(endpoint, self.token_id)
        response = self._send_mattermost_request(url, HttpMethod.GET)
        if response.status_code != HTTPStatus.OK:
            logging.warning("Cannot get owner token, probably bot has not enough permissions")
            return
        response_data = response.json()
        return response_data.get("user_id")

    def update_bot_settings(self, bot_id):
        endpoint = "bots"
        url = self._get_full_mattermost_url(endpoint, bot_id)
        response = self._send_mattermost_request(url, HttpMethod.PUT, json={
            "username": "robusta",
            "display_name": "Robusta"
        })
        if response.status_code != HTTPStatus.OK:
            logging.warning("Cannot update bot settings, probably bot has not enough permissions")
        self.update_bot_logo(bot_id)

    def update_bot_logo(self, bot_id):
        endpoint = f"users/{bot_id}/image"
        img_data = process_request(ROBUSTA_LOGO_URL, HttpMethod.GET).content
        url = self._get_full_mattermost_url(endpoint)
        response = self._send_mattermost_request(url, HttpMethod.POST, files=[("image", ("image", img_data))])
        if response.status_code != HTTPStatus.OK:
            logging.warning("Cannot update bot logo, probably bot has not enough permissions")

    def _init_setup(self):
        bot_id = self.get_token_owner_id()
        if bot_id:
            self.update_bot_settings(bot_id)

    def post_message(self, title, msg_attachments: List[Dict], file_attachments=None):
        file_attachments = file_attachments or []
        file_attachments = self.upload_files(file_attachments)
        endpoint = "posts"
        url = self._get_full_mattermost_url(endpoint)
        response = self._send_mattermost_request(url, HttpMethod.POST, json={
            "channel_id": self.channel_id,
            "message": title,
            "file_ids": file_attachments,
            "props": {
                "attachments": msg_attachments
            }
        })
        if response.status_code != HTTPStatus.CREATED:
            logging.error("Couldn't deliver mattermost bot message")

    def upload_files(self, files):
        endpoint = "files"
        file_ids = []
        url = self._get_full_mattermost_url(endpoint)
        for file in files:
            response = self._send_mattermost_request(url, HttpMethod.POST, files={
                "files": file,
                "channel_id": (None, self.channel_id),
                "filename": (None, file[0])
            })
            if response.status_code != HTTPStatus.CREATED:
                logging.error(f"There was an error uploading the file: {file[0]}")
                continue
            response = response.json()
            file_ids.append(response["file_infos"][0]["id"])
        return file_ids
