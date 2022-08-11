import logging
import uuid
import re
from datetime import datetime
from enum import Enum
from pydantic.main import BaseModel
from typing import List, Dict, Union

from ..model.env_vars import ROBUSTA_UI_DOMAIN
from ..reporting.consts import FindingSubjectType, FindingSource, FindingType
from ...core.discovery.top_service_resolver import TopServiceResolver
from requests import get

class BaseBlock(BaseModel):
    hidden: bool = False


class FindingSeverity(Enum):
    DEBUG = 0
    INFO = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4

    @staticmethod
    def from_severity(severity: str) -> "FindingSeverity":
        if severity == "DEBUG":
            return FindingSeverity.DEBUG
        elif severity == "INFO":
            return FindingSeverity.INFO
        elif severity == "LOW":
            return FindingSeverity.LOW
        elif severity == "MEDIUM":
            return FindingSeverity.MEDIUM
        elif severity == "HIGH":
            return FindingSeverity.HIGH

        raise Exception(f"Unknown severity {severity}")
    
    def to_emoji(self) -> str:
        if self == FindingSeverity.DEBUG: return "🔵"
        elif self == FindingSeverity.INFO: return "🟢"
        elif self == FindingSeverity.LOW: return "🟡"
        elif self == FindingSeverity.MEDIUM: return "🟠" 
        elif self ==  FindingSeverity.HIGH: return "🔴"



class Enrichment:
    # These is the actual enrichment data
    blocks: List[BaseBlock] = []
    # General purpose rendering flags, that can be used by specific sinks
    annotations: Dict[str, str] = {}

    def __init__(self, blocks: List[BaseBlock], annotations=None):
        if annotations is None:
            annotations = {}
        self.blocks = blocks
        self.annotations = annotations

    def __str__(self):
        return f"annotations: {self.annotations} Enrichment: {self.blocks} "


class Filterable:
    @property
    def attribute_map(self) -> Dict[str, str]:
        raise NotImplementedError

    def get_invalid_attributes(self, attributes: List[str]) -> List:
        return list(set(attributes) - set(self.attribute_map))

    def attribute_matches(self, attribute: str, expression: Union[str, List[str]]) -> bool:
        value = self.attribute_map[attribute]
        if isinstance(expression, str):
            return bool(re.match(expression, value))
        else:  # expression is list of values
            return value in expression

    def matches(self, requirements: Dict[str, Union[str, List[str]]]) -> bool:
        invalid_attributes = self.get_invalid_attributes(list(requirements.keys()))
        if len(invalid_attributes) > 0:
            logging.warning(f"Invalid match attributes: {invalid_attributes}")
            return False

        for attribute, expression in requirements.items():
            if not self.attribute_matches(attribute, expression):
                return False
        return True


class FindingSubject:
    def __init__(
        self,
        name: str = None,
        subject_type: FindingSubjectType = FindingSubjectType.TYPE_NONE,
        namespace: str = None,
        node: str = None,
    ):
        self.name = name
        self.subject_type = subject_type
        self.namespace = namespace
        self.node = node


class Finding(Filterable):
    """
    A Finding represents an event that should be sent to sinks.
    """

    def __init__(
        self,
        title: str,
        aggregation_key: str,
        severity: FindingSeverity = FindingSeverity.INFO,
        source: FindingSource = FindingSource.NONE,
        description: str = None,
        subject: FindingSubject = FindingSubject(),
        finding_type: FindingType = FindingType.ISSUE,
        failure: bool = True,
        creation_date: str = None,
        fingerprint: str = None,
        starts_at: datetime = None,
        ends_at: datetime = None,
        add_silence_url: bool = False
    ) -> None:
        self.id: uuid = uuid.uuid4()
        self.title = title
        self.finding_type = finding_type
        self.failure = failure
        self.description = description
        self.source = source
        self.aggregation_key = aggregation_key
        self.severity = severity
        self.category = None  # TODO fill real category
        self.subject = subject
        self.enrichments: List[Enrichment] = []
        self.service_key = TopServiceResolver.guess_service_key(
            name=subject.name, namespace=subject.namespace
        )
        uri_path = (
            f"services/{self.service_key}?tab=grouped" if self.service_key else "graphs"
        )
        self.investigate_uri = f"{ROBUSTA_UI_DOMAIN}/{uri_path}"
        self.add_silence_url = add_silence_url
        self.creation_date = creation_date
        self.fingerprint = fingerprint
        self.starts_at = starts_at if starts_at else datetime.now()
        self.ends_at = ends_at
        self.dirty = False

    @property
    def attribute_map(self) -> Dict[str, str]:
        return {
            "title": str(self.title),
            "identifier": str(self.aggregation_key),
            "severity": str(self.severity.name),
            "source": str(self.source.name),
            "type": str(self.finding_type.name),
            "kind": str(self.subject.subject_type.value),
            "namespace": str(self.subject.namespace),
            "node": str(self.subject.node),
            "name": str(self.subject.name),
        }

    def add_enrichment(self, enrichment_blocks: List[BaseBlock], annotations=None, suppress_warning: bool = False):
        if self.dirty and not suppress_warning:
            logging.warning("Updating a finding after it was added to the event is not allowed!")

        if not enrichment_blocks:
            return
        if annotations is None:
            annotations = {}
        self.enrichments.append(Enrichment(enrichment_blocks, annotations))

    def __str__(self):
        return f"title: {self.title} desc: {self.description} severity: {self.severity} sub-name: {self.subject.name} sub-type:{self.subject.subject_type.value} enrich: {self.enrichments}"

    def get_prometheus_silence_url(self, cluster_id: str) -> str:
        labels: Dict[str, str] = {
            "alertname": self.aggregation_key,
            "cluster": cluster_id
        }
        if self.subject.namespace:
            labels["namespace"] = self.subject.namespace

        kind: str = self.subject.subject_type.value
        if kind and self.subject.name:
            labels[kind] = self.subject.name

        labels["referer"] = "sink"

        uri = get(f"{ROBUSTA_UI_DOMAIN}/silences/create", labels)
        return uri.url
