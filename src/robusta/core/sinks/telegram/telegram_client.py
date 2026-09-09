import logging
import os
from typing import Union

import requests

from robusta.core.reporting.utils import PNG_SUFFIX, SVG_SUFFIX, convert_svg_to_png, is_image
from robusta.core.sinks.telegram.telegram_html import split_telegram_html

TELEGRAM_BASE_URL = os.environ.get("TELEGRAM_BASE_URL", "https://api.telegram.org")


class TelegramClient:
    def __init__(self, chat_id: Union[int, str], thread_id: int, bot_token: str):
        self.chat_id = int(chat_id)
        self.thread_id = thread_id
        self.bot_token = bot_token

    def send_message(self, message: str, disable_links_preview: bool = True):
        """Send one or more HTML sendMessage calls. Oversized text is split, never attached as a file."""
        chunks = split_telegram_html(message)
        if not chunks:
            return
        for chunk in chunks:
            self._send_message_chunk(chunk, disable_links_preview=disable_links_preview)

    def _send_message_chunk(self, message: str, disable_links_preview: bool = True):
        url = f"{TELEGRAM_BASE_URL}/bot{self.bot_token}/sendMessage"
        message_json = {
            "chat_id": self.chat_id,
            "message_thread_id": self.thread_id,
            # HTML is required for <blockquote expandable>. Do not use MarkdownV2
            # (open PR robusta-dev/robusta#2105 / issue #1982); that path cannot
            # express expandable quotes. Related UX: #2137.
            "parse_mode": "HTML",
            "text": message,
            "link_preview_options": {"is_disabled": disable_links_preview},
        }
        response = requests.post(url, json=message_json)

        if response.status_code != 200:
            logging.error(
                f"Failed to send telegram message: chat_id - {self.chat_id} reason - {response.reason} {response.text}"
            )

    def send_file(self, file_name: str, contents: bytes):
        file_type = "Photo" if is_image(file_name) else "Document"
        url = f"{TELEGRAM_BASE_URL}/bot{self.bot_token}/send{file_type}"
        if file_name.endswith(SVG_SUFFIX):
            contents = convert_svg_to_png(contents)
            file_name = file_name.replace(SVG_SUFFIX, PNG_SUFFIX)

        data = {"chat_id": self.chat_id}
        if self.thread_id is not None:
            data["message_thread_id"] = self.thread_id
        files = {file_type.lower(): (file_name, contents)}
        response = requests.post(url, data=data, files=files)

        if response.status_code != 200:
            logging.error(
                f"Failed to send telegram file: chat_id - {self.chat_id} reason - {response.reason} {response.text}"
            )
