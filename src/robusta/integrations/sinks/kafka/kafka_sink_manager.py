import threading
from collections import defaultdict

from kafka import KafkaProducer

from .kafka_sink import KafkaSink
from ..sink_base import SinkBase


class KafkaSinkManager:

    manager_lock = threading.Lock()
    producers_map = defaultdict(None)

    @staticmethod
    def get_kafka_sink(kafka_url : str, topic: str) -> SinkBase:
        with KafkaSinkManager.manager_lock:
            producer = KafkaSinkManager.producers_map.get(kafka_url)
            if producer is not None:
                return KafkaSink(producer, topic)
            producer = KafkaProducer(bootstrap_servers=kafka_url)
            KafkaSinkManager.producers_map[kafka_url] = producer
            return KafkaSink(producer, topic)
