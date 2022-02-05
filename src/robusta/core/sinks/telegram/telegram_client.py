import logging
import os
import requests

from ....core.reporting.utils import convert_svg_to_png, is_image, SVG_SUFFIX, PNG_SUFFIX

TELEGRAM_BASE_URL = os.environ.get("TELEGRAM_BASE_URL", "https://api.telegram.org")


class TelegramClient:
    def __init__(self, chat_id: int, bot_token: str):
        self.chat_id = chat_id
        self.bot_token = bot_token

    def send_message(self, message: str, disable_links_preview: bool = True):
        url = f"{TELEGRAM_BASE_URL}/bot{self.bot_token}/sendMessage"
        message_json = {
            "chat_id": self.chat_id,
            "disable_web_page_preview": disable_links_preview,
            "parse_mode": "Markdown",
            "text": message
        }
        response = requests.post(url, json=message_json)

        if response.status_code != 200:
            logging.error(
                f"Failed to send telegram message: chat_id - {self.chat_id} reason - {response.reason} {response.text}"
            )

    def send_file(self, file_name: str, contents: bytes):
        file_type = "Photo" if is_image(file_name) else "Document"
        url = f"{TELEGRAM_BASE_URL}/bot{self.bot_token}/send{file_type}?chat_id={self.chat_id}"
        if file_name.endswith(SVG_SUFFIX):
            contents = convert_svg_to_png(contents)
            file_name = file_name.replace(SVG_SUFFIX, PNG_SUFFIX)

        files = {
            file_type.lower(): (file_name, contents)
        }
        response = requests.post(url, files=files)

        if response.status_code != 200:
            logging.error(
                f"Failed to send telegram file: chat_id - {self.chat_id} reason - {response.reason} {response.text}"
            )

