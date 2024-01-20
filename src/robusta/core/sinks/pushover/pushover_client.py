import logging

import requests

from robusta.core.reporting.utils import PNG_SUFFIX, SVG_SUFFIX, convert_svg_to_png, is_image

class PushoverClient:
    def __init__(self, token: str, user: str, device: str, pushover_url: str):
        self.token = str(token)
        self.user = str(user)
        self.device = str(device)
        self.pushover_url = str(pushover_url)

    def send_message(self, title: str, message: str, send_as_html: bool, additional_url: str):
        message_json = {
            "token": self.token,
            "user": self.user,
            "html": 1 if send_as_html else "",
            "title": title,
            "message": message,
            "url": additional_url,
            "device": self.device
        }

        response = requests.post(self.pushover_url, json=message_json)

        if response.status_code != 200:
            logging.error(
                f"Failed to send pushover message with reason being: {response.reason} {response.text}"
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

        response = requests.post(self.pushover_url, json=message_json, files=files)

        if response.status_code != 200:
            logging.error(
                f"Failed to send pushover message with reason being: {response.reason} {response.text}"
            )
