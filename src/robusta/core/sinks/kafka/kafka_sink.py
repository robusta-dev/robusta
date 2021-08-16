import json
import logging

from pydantic import BaseModel
from kafka import KafkaProducer

from ..sink_config import SinkConfigBase
from ...reporting.blocks import Finding, Enrichment, KubernetesDiffBlock, JsonBlock
from ..sink_base import SinkBase


class KafkaSinkConfig(BaseModel):
    kafka_url: str
    topic: str


class KafkaSink(SinkBase):
    def __init__(self, sink_config: SinkConfigBase):
        super().__init__(sink_config)
        config = KafkaSinkConfig(**sink_config.params)
        self.producer = KafkaProducer(bootstrap_servers=config.kafka_url)
        self.topic = config.topic

    def write_finding(self, finding: Finding):
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
