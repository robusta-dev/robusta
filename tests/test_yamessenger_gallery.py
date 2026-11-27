import unittest
from email import policy
from email.parser import BytesParser
from unittest.mock import Mock, patch

import requests

from robusta.core.reporting.base import Finding
from robusta.core.reporting.blocks import FileBlock, TableBlock
from robusta.core.sinks.yamessenger.yamessenger_sink import YaMessengerSink
from robusta.core.sinks.yamessenger.yamessenger_sink_params import YaMessengerSinkConfigWrapper, YaMessengerSinkParams


class YaMessengerGalleryTest(unittest.TestCase):
    def setUp(self):
        self.finding = Finding(title="Test alert", aggregation_key="test")
        self.finding.add_enrichment(
            [FileBlock("graph.png", b"png-data"), FileBlock("details.txt", b"details"), TableBlock([["value"]])]
        )
        self.post = self.enterContext(patch("robusta.core.sinks.yamessenger.yamessenger_client.requests.post"))
        self.post.return_value.status_code = 200
        self.post.return_value.json.return_value = {"ok": True}

    def send(self, **options):
        config = YaMessengerSinkParams(
            name="telemost", bot_token="test-token", chat_id="0/0/test", disable_notifications=True, **options
        )
        registry = Mock()
        registry.get_global_config.return_value = {"cluster_name": "test-cluster"}
        sink = YaMessengerSink(YaMessengerSinkConfigWrapper(yamessenger_sink=config), registry)
        sink.write_finding(self.finding, platform_enabled=False)

    def endpoints(self):
        return [call.args[0].rsplit("/messages/", 1)[1].strip("/") for call in self.post.call_args_list]

    def test_gallery_sends_caption_and_images_in_one_request(self):
        self.finding.add_enrichment([FileBlock("second.jpg", b"jpg-data")])
        self.send(send_images_as_gallery=True, send_documents=False, mark_important=True)
        self.assertEqual(self.endpoints(), ["sendGallery"])
        call = self.post.call_args
        self.assertEqual(call.kwargs["headers"]["Authorization"], "OAuth test-token")
        request = requests.Request("POST", call.args[0], data=call.kwargs["data"], files=call.kwargs["files"]).prepare()
        mime_header = f"Content-Type: {request.headers['Content-Type']}\r\n\r\n".encode()
        parts = list(BytesParser(policy=policy.default).parsebytes(mime_header + request.body).iter_parts())
        files = [part for part in parts if part.get_param("name", header="content-disposition") == "images"]
        self.assertEqual([part.get_filename() for part in files], ["graph.png", "second.jpg"])
        self.assertEqual([part.get_payload(decode=True) for part in files], [b"png-data", b"jpg-data"])
        self.assertIn("Test alert", call.kwargs["data"]["text"])
        self.assertEqual(call.kwargs["data"]["chat_id"], "0/0/test")
        self.assertEqual(call.kwargs["data"]["disable_notification"], "true")
        self.assertEqual(call.kwargs["data"]["important"], "true")

    def test_legacy_mode_still_sends_separate_attachments(self):
        self.send()
        self.assertEqual(self.endpoints(), ["sendText", "sendImage", "sendFile", "sendFile"])

    def test_table_render_failure_preserves_text_in_both_modes(self):
        for gallery in (False, True):
            with self.subTest(gallery=gallery), patch.object(TableBlock, "render_rows", side_effect=ValueError):
                self.post.reset_mock()
                with self.assertRaises(ValueError):
                    self.send(send_images_as_gallery=gallery)
                self.assertEqual(self.endpoints(), ["sendText"])
                self.assertIn("Test alert", self.post.call_args.kwargs["json"]["text"])

    def test_gallery_image_preparation_failure_sends_text(self):
        with patch(
            "robusta.core.sinks.yamessenger.yamessenger_client.YaMessengerClient._prepare_file", side_effect=ValueError
        ):
            self.send(send_images_as_gallery=True, send_documents=False)
        self.assertEqual(self.endpoints(), ["sendText"])

    def test_gallery_respects_send_files_false(self):
        self.send(send_images_as_gallery=True, send_files=False)
        self.assertEqual(self.endpoints(), ["sendText"])

    def test_explicit_gallery_rejection_falls_back_to_text(self):
        self.post.side_effect = [Mock(status_code=400), Mock(status_code=200)]
        self.send(send_images_as_gallery=True, send_documents=False)
        self.assertEqual(self.endpoints(), ["sendGallery", "sendText"])

    def test_gallery_can_keep_documents_as_separate_posts(self):
        self.send(send_images_as_gallery=True)
        self.assertEqual(self.endpoints(), ["sendGallery", "sendFile", "sendFile"])

    def test_timeout_does_not_send_a_duplicate_text_message(self):
        self.post.side_effect = requests.Timeout
        with self.assertRaises(requests.Timeout):
            self.send(send_images_as_gallery=True)
        self.assertEqual(self.endpoints(), ["sendGallery"])

    def test_gallery_without_images_uses_text_and_optional_documents(self):
        self.finding = Finding(title="Test alert", aggregation_key="test")
        self.finding.add_enrichment([FileBlock("details.txt", b"details")])
        self.send(send_images_as_gallery=True)
        self.assertEqual(self.endpoints(), ["sendText", "sendFile"])
