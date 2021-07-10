import json

from ..sink_base import SinkBase
from kafka import KafkaProducer


class KafkaSink(SinkBase):
    def __init__(self, producer: KafkaProducer, topic: str):
        self.producer = producer
        self.topic = topic

    def write(self, data: dict):
        self.producer.send(self.topic, value=json.dumps(data).encode("utf-8"))
