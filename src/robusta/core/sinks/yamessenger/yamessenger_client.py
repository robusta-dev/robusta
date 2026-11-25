import logging
import mimetypes
import os
import uuid

import requests

from robusta.core.reporting.utils import SVG_SUFFIX, convert_svg_to_png, is_image

YM_API_BASE_URL = os.environ.get("YM_API_BASE_URL", "https://botapi.messenger.yandex.net")
YM_API_SEND_TEXT_ENDPOINT = "/bot/v1/messages/sendText"
YM_API_SEND_FILE_ENDPOINT = "/bot/v1/messages/sendFile"
YM_API_SEND_IMAGE_ENDPOINT = "/bot/v1/messages/sendImage"
YM_API_SEND_GALLERY_ENDPOINT = "/bot/v1/messages/sendGallery/"


class YaMessengerClient:
    def __init__(
        self,
        bot_token: str,
        chat_id: str,
        user_name: str,
        disable_notifications: bool,
        disable_links_preview: bool,
        mark_important: bool,
    ):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.user_name = user_name
        self.disable_notifications = disable_notifications
        self.disable_links_preview = disable_links_preview
        self.mark_important = mark_important

    def send_message(self, message: str):
        url = f"{YM_API_BASE_URL}{YM_API_SEND_TEXT_ENDPOINT}"

        headers = {"Authorization": f"OAuth {self.bot_token}"}

        request = {
            "disable_notification": self.disable_notifications,
            "disable_preview": self.disable_links_preview,
            "important": self.mark_important,
            "payload_id": str(uuid.uuid4()),
            "text": message,
        }

        if self.user_name:
            request["login"] = self.user_name
        else:
            request["chat_id"] = self.chat_id

        response = requests.post(url, headers=headers, json=request)

        if response.status_code != 200:
            logging.error(
                f"Failed to send a message via Yandex.Messenger, chat_id:{self.chat_id} reason:{response.reason} response:{response.text})"
            )

    @staticmethod
    def _prepare_file(file_name: str, contents: bytes):
        if file_name.endswith(SVG_SUFFIX):
            try:
                png = convert_svg_to_png(contents)
                if png is not None:
                    file_name = file_name.removesuffix(SVG_SUFFIX) + ".png"
                    contents = png
            except Exception:
                logging.exception(f"Failed to convert an apparent SVG image to PNG, filename:{file_name}")
        return file_name, contents, mimetypes.guess_type(file_name, strict=False)[0]

    def send_gallery(self, message: str, images: list[tuple[str, bytes]]) -> bool:
        """Return false only when the API definitively rejects the gallery."""
        data = {
            "text": message,
            "disable_notification": str(self.disable_notifications).lower(),
            "important": str(self.mark_important).lower(),
        }
        if self.user_name:
            data["login"] = self.user_name
        else:
            data["chat_id"] = self.chat_id

        response = requests.post(
            f"{YM_API_BASE_URL}{YM_API_SEND_GALLERY_ENDPOINT}",
            headers={"Authorization": f"OAuth {self.bot_token}"},
            data=data,
            files=[("images", self._prepare_file(name, contents)) for name, contents in images],
            timeout=30,
        )
        if response.status_code in (400, 413, 415, 422):
            logging.warning(
                "Yandex Messenger rejected the gallery (HTTP %s); sending text instead", response.status_code
            )
            return False
        response.raise_for_status()
        if response.json().get("ok") is False:
            logging.warning("Yandex Messenger rejected the gallery; sending text instead")
            return False
        return True

    def send_file(self, file_name: str, contents: bytes):
        file_name, contents, content_type = self._prepare_file(file_name, contents)

        file_type = "image" if is_image(file_name) else "document"

        url = (
            f"{YM_API_BASE_URL}{YM_API_SEND_IMAGE_ENDPOINT}"
            if file_type == "image"
            else f"{YM_API_BASE_URL}{YM_API_SEND_FILE_ENDPOINT}"
        )

        headers = {"Authorization": f"OAuth {self.bot_token}"}

        request = {
            file_type: (file_name, contents, content_type),
        }

        if self.user_name:
            request["login"] = (None, self.user_name)
        else:
            request["chat_id"] = (None, self.chat_id)

        response = requests.post(url, headers=headers, files=request)

        if response.status_code != 200:
            logging.error(
                f"Failed to send a file via Yandex.Messenger, chat_id:{self.chat_id} reason:{response.reason} response:{response.text}"
            )
