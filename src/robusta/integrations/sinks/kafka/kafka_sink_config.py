from pydantic import BaseModel


class KafkaSinkConfig(BaseModel):
    kafka_url: str
    topic: str
