import json
import logging
from kafka import KafkaProducer

from .kafka_sink_params import KafkaSinkConfigWrapper
from ...reporting.blocks import KubernetesDiffBlock, JsonBlock
from ...reporting.base import Finding, Enrichment
from ..sink_base import SinkBase


class KafkaSink(SinkBase):
    def __init__(self, sink_config: KafkaSinkConfigWrapper):
        super().__init__(sink_config.kafka_sink)
        self.producer = KafkaProducer(
            bootstrap_servers=sink_config.kafka_sink.kafka_url
        )
        self.topic = sink_config.kafka_sink.topic

    def __eq__(self, other):
        return (
            isinstance(other, KafkaSink)
            and other.sink_name == self.sink_name
            and other.producer == self.producer
            and other.topic == self.topic
        )

    def write_finding(self, finding: Finding, platform_enabled: bool):
        for enrichment in finding.enrichments:
            self.send_enrichment(
                enrichment,
                finding.subject.name,
                finding.subject.subject_type.value,
                finding.subject.namespace,
            )

    def send_enrichment(
        self,
        enrichment: Enrichment,
        resource_name: str,
        resource_type: str,
        resource_namespace: str,
    ):
        kafka_blocks = [
            block
            for block in enrichment.blocks
            if (isinstance(block, KubernetesDiffBlock) or isinstance(block, JsonBlock))
        ]
        if not kafka_blocks:  # currently supporting sending kafka sink only diffs
            if len(enrichment.blocks) > 0:
                logging.warning(
                    "Kafka sink unsupported enrichment types. Currently only diff/json enrichment is supported"
                )
            return

        message_payload = ""
        for block in kafka_blocks:
            if isinstance(block, KubernetesDiffBlock):
                data = {
                    "resource_name": resource_name,
                    "resource_namespace": resource_namespace,
                    "resource_type": resource_type,
                    "message": f"{resource_type} properties change",
                    "changed_properties": [
                        {
                            "property": ".".join(attribute_diff.path),
                            "old": attribute_diff.other_value,
                            "new": attribute_diff.value,
                        }
                        for attribute_diff in block.diffs
                    ],
                }
                message_payload = json.dumps(data).encode("utf-8")
            elif isinstance(block, JsonBlock):
                message_payload = block.json_str.encode("utf-8")

            self.producer.send(self.topic, value=message_payload)
