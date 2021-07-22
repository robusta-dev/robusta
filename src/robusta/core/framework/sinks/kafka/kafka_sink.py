import json
import logging

from pydantic import BaseModel
import threading
from collections import defaultdict
from kafka import KafkaProducer

from ....reporting.blocks import Finding, Enrichment, DiffsBlock, JsonBlock
from ..sink_base import SinkBase


class KafkaSinkConfig(BaseModel):
    kafka_url: str
    topic: str


class KafkaSink(SinkBase):
    def __init__(self, producer: KafkaProducer, topic: str, sink_name: str):
        super().__init__(sink_name)
        self.producer = producer
        self.topic = topic

    def write(self, data: dict):
        self.producer.send(self.topic, value=json.dumps(data).encode("utf-8"))

    def write_finding(self, finding: Finding):
        for enrichment in finding.enrichments:
            self.send_enrichment(
                enrichment,
                finding.subject_name,
                finding.subject_type,
                finding.subject_namespace,
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
            if (isinstance(block, DiffsBlock) or isinstance(block, JsonBlock))
        ]
        if not kafka_blocks:  # currently supporting sending kafka sink only diffs
            if len(enrichment.blocks) > 0:
                logging.warning(
                    "Kafka sink unsupported enrichment types. Currently only diff/json enrichment is supported"
                )
            return

        message_payload = ""
        for block in kafka_blocks:
            if isinstance(block, DiffsBlock):
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


class KafkaSinkManager:

    manager_lock = threading.Lock()
    producers_map = defaultdict(None)

    @staticmethod
    def get_kafka_sink(sink_name: str, sink_config: KafkaSinkConfig) -> SinkBase:
        with KafkaSinkManager.manager_lock:
            producer = KafkaSinkManager.producers_map.get(sink_config.kafka_url)
            if producer is not None:
                return KafkaSink(producer, sink_config.topic, sink_name)
            producer = KafkaProducer(bootstrap_servers=sink_config.kafka_url)
            KafkaSinkManager.producers_map[sink_config.kafka_url] = producer
            return KafkaSink(producer, sink_config.topic, sink_name)
