import logging
import os

import requests

from robusta.core.reporting.utils import PNG_SUFFIX, SVG_SUFFIX, convert_svg_to_png, is_image

PUSHOVER_BASE_URL = os.environ.get("PUSHOVER_BASE_URL", "https://api.pushover.net/1/messages.json")


class PushoverClient:
    def __init__(self, token: str, user: str, device: str):
        self.token = str(token)
        self.user = str(user)
        self.device = str(device)

    def send_message(self, title: str, message: str, send_as_html: bool, additional_url: str):
        url = f"{PUSHOVER_BASE_URL}"
        message_json = {
            "token": self.token,
            "user": self.user,
            "html": 1 if send_as_html else "",
            "title": title,
            "message": message,
            "url": additional_url,
            "device": self.device
        }

        response = requests.post(url, json=message_json)

        if response.status_code != 200:
            logging.error(
                f"Failed to send pushover message: token - {self.token} reason - {response.reason} {response.text}"
            )

    def send_file(self, file_name: str, contents: bytes, title: str, message: str, send_as_html: bool, additional_url: str):
        # Pushover only supports images and text
        if is_image(file_name):
            file_type = "Photo"
        else:
            return
            
        if file_name.endswith(SVG_SUFFIX):
            contents = convert_svg_to_png(contents)
            file_name = file_name.replace(SVG_SUFFIX, PNG_SUFFIX)
        files = {file_type.lower(): (file_name, contents.decode())}

        url = f"{PUSHOVER_BASE_URL}"
        
        message_json = {
            "token": self.token,
            "user": self.user,
            "html": 1 if send_as_html else "",
            "title": title,
            "message": message,
            "attachement": files,
            "url": additional_url,
            "device": self.device
        }

        response = requests.post(url, json=message_json, files=files)

        if response.status_code != 200:
            logging.error(
                f"Failed to send pushover file: token - {self.token} reason - {response.reason} {response.text}"
            )
