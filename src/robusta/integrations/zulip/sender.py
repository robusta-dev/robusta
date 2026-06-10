import logging
from typing import List
from urllib.parse import urlencode

from requests.sessions import Session

from robusta.core.reporting import (
    EventsBlock,
    FileBlock,
    JsonBlock,
    KubernetesDiffBlock,
    ListBlock,
    MarkdownBlock,
    TableBlock,
    EmptyFileBlock,
)
from robusta.core.reporting.base import BaseBlock, Finding, FindingStatus, LinkType
from robusta.core.reporting.blocks import LinksBlock
from robusta.core.reporting.consts import FindingSource
from robusta.core.reporting.utils import convert_svg_to_png
from robusta.core.sinks.common import ChannelTransformer
from robusta.core.sinks.zulip.zulip_sink_params import ZulipSinkParams

ZULIP_MESSAGE_DEFAULT_LEN: int = 10_000


class ZulipSender:
    def __init__(
        self, api_url: str, stream_name: str, zclient: Session, account_id: str, cluster_name: str, signing_key: str
    ):
        self.signing_key = signing_key
        self.account_id = account_id
        self.cluster_name = cluster_name
        self.api_url = api_url
        self.zclient = zclient

        self.max_message_len = self.__get_max_msg_len()

        self.stream_name = stream_name
        self.stream_id = self.__get_stream_id(stream_name)
        self.topic_cache = self.__load_topics(self.stream_id)

    def __get_max_msg_len(self):
        try:
            r = self.zclient.post(f"{self.api_url}/api/v1/register")
            r.raise_for_status()
            return int(r.json()["max_message_length"])

        except Exception as e:
            logging.exception(
                f"Zulip Sink: failed to fetch max_message_length: {e}. Using default value of: {ZULIP_MESSAGE_DEFAULT_LEN}"
            )
            return ZULIP_MESSAGE_DEFAULT_LEN

    def __to_zulip_bold(self, text: str):
        return f"**{text}**"

    def __to_zulip_block(self, text: str, text_type: str = "text"):
        return f"```{text_type}\n{text}\n```"

    def __to_zulip_list(self, items: List[str]):
        return "\n".join([f"* {item}" for item in items])

    def __to_zulip_link(self, name: str, url: str):
        return f"[{name}]({url})"

    def __to_zulip_table(self, block: TableBlock):
        return block.to_table_string(table_fmt="pipe")

    def __build_msg_data(self, stream_name: str, topic: str, content: str):
        return {"type": "stream", "to": stream_name, "topic": topic, "content": content}

    def __get_stream_id(self, stream_name: str) -> int | None:
        try:
            params = {"stream": stream_name}
            r = self.zclient.get(f"{self.api_url}/api/v1/get_stream_id?{urlencode(params)}")
            r.raise_for_status()

            return int(r.json()["stream_id"])
        except Exception as e:
            logging.exception(f"Zulip Sink: failed to fetch stream_id: {e}")

    def __load_topics(self, stream_id: int | None):
        if stream_id is None:
            logging.warning("stream_id is None")
            return []

        try:
            r = self.zclient.get(f"{self.api_url}/api/v1/users/me/{stream_id}/topics")
            r.raise_for_status()

            topics = r.json().get("topics", [])
            logging.debug(f"topics: {topics}")

            return topics
        except Exception as e:
            logging.exception(f"Zulip Sink: could not fetch topics for stream: {stream_id}: {e}")
            return []

    # because there's no direct topic access, they are only identifiable by a message they are part of
    def __find_msg_id_for_topic_title(self, title_name: str) -> int | None:
        def find_msg_id(topics, title):
            return [topic["max_id"] for topic in topics if topic["name"] == title or topic["name"] == f"✔ {title}"]

        msg_id = find_msg_id(self.topic_cache, title_name)

        if not msg_id:
            self.topic_cache = self.__load_topics(self.stream_id)
            msg_id = find_msg_id(self.topic_cache, title_name)

        if len(msg_id) > 1:
            logging.warning(f"Zulip Sink: found multiple topics: {msg_id} that match the title: {title_name}")

        if len(msg_id) == 0:
            logging.warning(f"Zulip Sink: topic not found: {title_name}")

        return msg_id[0] if msg_id else None

    def __upload_to_zulip(self, filename: str, content: bytes):
        try:
            r = self.zclient.post(f"{self.api_url}/api/v1/user_uploads", files={filename: content})
            r.raise_for_status()
            uri = r.json()["uri"]
            return f"{self.api_url}{uri}"
        except Exception as e:
            logging.exception(f"Zulip Sink: failed to upload file: {e}")
            return ""

    def __create_finding_header(self, finding: Finding, status: FindingStatus):
        title = finding.title.removeprefix("[RESOLVED] ")
        sev = finding.severity

        if finding.source == FindingSource.PROMETHEUS:
            status_name: str = (
                f"{status.to_emoji()} `Prometheus Alert Firing` {status.to_emoji()}"
                if status == FindingStatus.FIRING
                else f"{status.to_emoji()} *Prometheus resolved*"
            )
        elif finding.source == FindingSource.KUBERNETES_API_SERVER:
            status_name: str = "👀 *K8s event detected*"
        else:
            status_name: str = "👀 *Notification*"
        return f"""{status_name} {sev.to_emoji()} {self.__to_zulip_bold(sev.name.capitalize())}
{title}"""

    def __enough_msg_bytes_free(self, message: str, added: str):
        return (len(message) + len(added)) <= self.max_message_len

    def __convert_svg_to_png(self, block: FileBlock):
        fname = block.filename
        contents = block.contents
        converted = convert_svg_to_png(block.contents)
        if converted is not None:
            contents = converted
            fname = fname.replace(".svg", ".png")
        return fname, contents

    def __to_zulip(self, block: BaseBlock, log_preview_char_limit: int, send_svg: bool):
        if isinstance(block, TableBlock):
            yield self.__to_zulip_table(block)
        elif isinstance(block, ListBlock):
            yield self.__to_zulip_list(block.items)
        elif isinstance(block, EventsBlock):
            yield self.__to_zulip_table(block)
        elif isinstance(block, MarkdownBlock):
            yield self.__to_zulip_block(block.text, "md")
        elif isinstance(block, KubernetesDiffBlock):
            for d in block.diffs:
                yield f"{self.__to_zulip_bold('.'.join(d.path))}: {d.other_value} ➡️ {d.value})"
        elif isinstance(block, LinksBlock):
            for link in block.links:
                yield self.__to_zulip_link(link.text, link.url)
        elif isinstance(block, JsonBlock):
            yield self.__to_zulip_block(block.json_str, "json")
        elif isinstance(block, FileBlock):
            if block.is_text_file() and log_preview_char_limit != 0:
                log_text = block.truncate_content(log_preview_char_limit).decode()
                yield f"📜 Logs:\n{self.__to_zulip_block(log_text)}"
            else:
                fname = block.filename
                contents = block.contents
                if fname.endswith(".svg") and not send_svg:
                    fname, contents = self.__convert_svg_to_png(block)
                file_link = self.__upload_to_zulip(fname, contents)
                yield self.__to_zulip_link(fname, file_link)
        elif not isinstance(block, EmptyFileBlock):
            logging.warning(f"Zulip Sink: cannot convert block of type {type(block)} to a zulip format block: {block}")

    def send_finding_to_zulip(self, finding: Finding, sink_params: ZulipSinkParams, platform_enabled: bool):
        status: FindingStatus = (
            FindingStatus.RESOLVED if finding.title.startswith("[RESOLVED]") else FindingStatus.FIRING
        )
        title = self.__create_finding_header(finding, status)

        message_lines: List[str] = [title]
        if platform_enabled:
            investigate_uri = finding.get_investigate_uri(self.account_id, self.cluster_name)
            message_lines.append(self.__to_zulip_link("🔎 Investigate", investigate_uri))
            if finding.add_silence_url:
                silence_url = finding.get_prometheus_silence_url(self.account_id, self.cluster_name)
                message_lines.append(self.__to_zulip_link("🔕 Silence", silence_url))

        for link in finding.links:
            message_lines.append(f"🎬 {self.__to_zulip_link(link.name, link.url)}")

        message_lines.append(f"{self.__to_zulip_bold('Source:')} `{self.cluster_name}`")
        message_lines.append(finding.description)

        for enrichment in finding.enrichments:
            for block in enrichment.blocks:
                message_lines.extend(self.__to_zulip(block, sink_params.log_preview_char_limit, sink_params.send_svg))

        message = ""
        for line in filter(None, message_lines):
            formatted_line = f"{line}\n\n"
            if self.__enough_msg_bytes_free(message, formatted_line):
                message += formatted_line

        try:
            if sink_params.topic_autoresolve and finding.source == FindingSource.PROMETHEUS:
                title = finding.title.removeprefix("[RESOLVED] ")
                msg_id = self.__find_msg_id_for_topic_title(title)

                logging.warning(f"sending with msg_id: {msg_id}")
                channel_topic = "✔ " + title if status == FindingStatus.RESOLVED and msg_id else title

                data = self.__build_msg_data(self.stream_name, channel_topic, message)

                r = self.zclient.post(f"{self.api_url}/api/v1/messages", data=data)
                if msg_id:
                    patch_data = {"topic": channel_topic, "propagate_mode": "change_all"}
                    r = self.zclient.patch(f"{self.api_url}/api/v1/messages/{msg_id}", data=patch_data)

                r.raise_for_status()
            else:
                channel_topic = ChannelTransformer.template(
                    sink_params.topic_override,
                    sink_params.topic_name,
                    self.cluster_name,
                    finding.subject.labels,
                    finding.subject.annotations,
                )
                data = self.__build_msg_data(self.stream_name, channel_topic, message)

                r = self.zclient.post(f"{self.api_url}/api/v1/messages", data=data)
                r.raise_for_status()
        except Exception as e:
            logging.exception(f"Zulip Sink: failed to send data: {e}")
