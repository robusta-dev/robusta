import logging
from http import HTTPStatus
from typing import List, Dict
from urllib.parse import urlparse

from ..common.requests import process_request, HttpMethod
from ...core.model.env_vars import ROBUSTA_LOGO_URL

_API_PREFIX = "api/v4"


class MattermostClient:
    channel_id: str
    bot_id: str

    def __init__(
            self, url: str, token: str, token_id: str, channel_name: str, schema: str
    ):
        """
        Set the Mattermost webhook url.
        """
        parsed_url = urlparse(url)
        # if netloc is empty string, the url was provided without schema
        if not parsed_url.netloc:
            self.client_url = urlparse("//" + url.split("//")[-1]).netloc
            self.schema = schema
        else:
            self.client_url = parsed_url.netloc
            self.schema = parsed_url.scheme

        self.token = token
        self.token_id = token_id
        self._init_setup(channel_name)

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

    def _init_setup(self, channel_name):
        bot_id = self.get_token_owner_id()
        self.channel_id = self.get_channel_id(channel_name)
        if not self.channel_id:
            logging.warning("No channel found, messages won't be sent")
        if bot_id:
            self.bot_id = bot_id
            self.update_bot_settings(bot_id)

    def get_channel_id(self, channel_name):
        endpoint = 'channels/search'
        url = self._get_full_mattermost_url(endpoint)
        response = self._send_mattermost_request(url, HttpMethod.POST, json={
            "term": channel_name
        })
        if response.status_code == HTTPStatus.OK:
            response = response.json()
            if not len(response):
                return None
            return response[0].get("id")

    def post_message(self, title, msg_attachments: List[Dict], file_attachments=None):
        if not self.channel_id:
            logging.warning("No channel found, messages won't be sent")
            return
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
