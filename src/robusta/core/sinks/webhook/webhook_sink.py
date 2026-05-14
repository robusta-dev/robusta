import json
import logging
import textwrap
from typing import List

import requests

from robusta.core.reporting import HeaderBlock, JsonBlock, KubernetesDiffBlock, ListBlock, MarkdownBlock
from robusta.core.reporting.base import BaseBlock, Finding
from robusta.core.sinks.sink_base import SinkBase
from robusta.core.sinks.transformer import Transformer
from robusta.core.sinks.webhook.webhook_sink_params import WebhookSinkConfigWrapper


class WebhookSink(SinkBase):
    def __init__(self, sink_config: WebhookSinkConfigWrapper, registry):
        super().__init__(sink_config.webhook_sink, registry)

        self.url = sink_config.webhook_sink.url
        self.format = sink_config.webhook_sink.format
        self.headers = (
            {"Authorization": sink_config.webhook_sink.authorization.get_secret_value()}
            if sink_config.webhook_sink.authorization
            else None
        )
        self.size_limit = sink_config.webhook_sink.size_limit
        self.slack_webhook = sink_config.webhook_sink.slack_webhook

    def write_finding(self, finding: Finding, platform_enabled: bool):
        if self.format == "text":
            self.__write_text(finding, platform_enabled)
        elif self.format == "json":
            self.__write_json(finding, platform_enabled)
        else:
            logging.exception(f"Webhook format {self.format} is not supported")

    def __write_text(self, finding: Finding, platform_enabled: bool):
        message_lines: List[str] = [finding.title]
        if platform_enabled:
            message_lines.append(f"Investigate: {finding.get_investigate_uri(self.account_id, self.cluster_name)}")

            if finding.add_silence_url:
                message_lines.append(
                    f"Silence: {finding.get_prometheus_silence_url(self.account_id, self.cluster_name)}"
                )

        for link in finding.links:
            message_lines.append(f"{link.name}: {link.url}")

        message_lines.append(f"Source: {self.cluster_name}")
        message_lines.append(finding.description)

        message = ""

        for enrichment in finding.enrichments:
            for block in enrichment.blocks:
                message_lines.extend(self.__to_unformatted_text(block))

        for line in [line for line in message_lines if line]:
            wrapped = textwrap.dedent(
                f"""
                {line}
                """
            )
            if len(message.encode('utf-8')) + len(wrapped.encode('utf8')) >= self.size_limit:
                break
            message += wrapped

        try:
            r = requests.post(self.url, data=message.encode('utf-8'), headers=self.headers)
            r.raise_for_status()
        except Exception:
            logging.exception(f"Webhook request error\n headers: \n{self.headers}")

    def __write_json(self, finding: Finding, platform_enabled: bool):
        finding_dict = {
            "title": finding.title,
            "description": finding.description,
            "cluster_name": self.cluster_name,
            "account_id": self.account_id,
            "severity": finding.severity.name,
            "source": finding.source.name,
            "finding_type": finding.finding_type.name,
            "aggregation_key": finding.aggregation_key,
            "failure": finding.failure,
            "fingerprint": finding.fingerprint,
            "starts_at": finding.starts_at.isoformat() if finding.starts_at else None,
            "ends_at": finding.ends_at.isoformat() if finding.ends_at else None,
            "id": str(finding.id),
            "category": finding.category,
            "service": json.loads(
                json.dumps(finding.service, default=lambda o: getattr(o, '__dict__', str(o)))
            ) if finding.service else None,
            "service_key": finding.service_key,
            "creation_date": finding.creation_date,
            "investigate_uri": finding.investigate_uri,
            "add_silence_url": finding.add_silence_url,
            "subject": {
                "name": finding.subject.name,
                "kind": finding.subject.subject_type.value,
                "namespace": finding.subject.namespace,
                "node": finding.subject.node,
                "container": finding.subject.container,
                "labels": finding.subject.labels,
                "annotations": finding.subject.annotations,
            },
            "links": [
                {"name": link.name, "url": link.url, "type": link.type.value if link.type else None}
                for link in finding.links
            ],
        }

        if platform_enabled:
            finding_dict["investigate"] = finding.get_investigate_uri(self.account_id, self.cluster_name)
            if finding.add_silence_url:
                finding_dict["silence"] = finding.get_prometheus_silence_url(self.account_id, self.cluster_name)

        # Enrichments last so they're the first thing dropped if size_limit is exceeded.
        finding_dict["enrichments"] = json.loads(
            json.dumps(finding.enrichments, default=lambda o: getattr(o, '__dict__', str(o)))
        )

        message = {}
        message_length = 0

        for key, value in finding_dict.items():
            pair_length = len(json.dumps({key: value}).encode('utf-8'))

            if message_length + pair_length <= self.size_limit:
                message[key] = value
                message_length += pair_length
            else:
                break
        if self.slack_webhook:
            labels = message.get('subject', {}).get('labels')
            if labels:
                labels_as_text = ", ".join(f"{k}: {v}" for k, v in labels.items())
            else:
                labels_as_text = None
            message = {
                "text": f"*Title:* {message['title']}\n"
                f"*Description:* {message['description']}\n"
                f"*Failure:* {message['failure']}\n"
                f"*Aggregation Key:* {message['aggregation_key']}\n"
                f"*labels*: {labels_as_text}\n"
            }
        try:
            r = requests.post(self.url, json=message, headers=self.headers)
            r.raise_for_status()
        except Exception:
            logging.exception(f"Webhook request error\n headers: \n{self.headers}")

    @classmethod
    def __to_clear_text(cls, markdown_text: str) -> str:
        # just create a readable links format
        links = Transformer.get_markdown_links(markdown_text)
        for link in links:
            # take only the data between the first '<' and last '>'
            splits = link[1:-1].split("|")
            if len(splits) == 2:  # don't replace unexpected strings
                replacement = f"{splits[1]}: {splits[0]}"
                markdown_text = markdown_text.replace(link, replacement)

        return markdown_text

    def __to_unformatted_text(cls, block: BaseBlock) -> List[str]:
        lines = []
        if isinstance(block, HeaderBlock):
            lines.append(block.text)
        elif isinstance(block, ListBlock):
            lines.extend([cls.__to_clear_text(item) for item in block.items])
        elif isinstance(block, MarkdownBlock):
            lines.append(cls.__to_clear_text(block.text))
        elif isinstance(block, JsonBlock):
            lines.append(block.json_str)
        elif isinstance(block, KubernetesDiffBlock):
            for diff in block.diffs:
                lines.append(f"*{'.'.join(diff.path)}*: {diff.other_value} ==> {diff.value}")
        return lines
