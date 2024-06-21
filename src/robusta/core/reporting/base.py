import hashlib
import logging
import re
import urllib.parse
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlencode

from pydantic.main import BaseModel

from robusta.core.discovery.top_service_resolver import TopServiceResolver
from robusta.core.model.env_vars import ROBUSTA_UI_DOMAIN
from robusta.core.reporting.consts import FindingSource, FindingSubjectType, FindingType
from robusta.integrations.kubernetes.api_client_utils import get_namespace_labels
from robusta.utils.scope import BaseScopeMatcher


class BaseBlock(BaseModel):
    hidden: bool = False
    html_class: str = None


class Emojis(Enum):
    Explain = "📘"
    Recommend = "🛠"
    Alert = "🚨"
    K8Notification = "👀"


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
        if self == FindingSeverity.DEBUG:
            return "🔵"
        elif self == FindingSeverity.INFO:
            return "⚪️"
        elif self == FindingSeverity.LOW:
            return "🟡"
        elif self == FindingSeverity.MEDIUM:
            return "🟠"
        elif self == FindingSeverity.HIGH:
            return "🔴"


class FindingStatus(Enum):
    FIRING = 0
    RESOLVED = 1

    def to_color_hex(self) -> str:
        if self == FindingStatus.RESOLVED:
            return "#00B302"

        return "#EF311F"

    def to_color_decimal(self) -> str:
        if self == FindingStatus.RESOLVED:
            return "45826"

        return "15675679"

    def to_emoji(self) -> str:
        if self == FindingStatus.RESOLVED:
            return "✅"

        return "🔥"


class VideoLink(BaseModel):
    url: str
    name: str = "See more"


class EnrichmentType(Enum):
    graph = "graph"
    ai_analysis = "ai_analysis"
    node_info = "node_info"
    container_info = "container_info"
    k8s_events = "k8s_events"
    alert_labels = "alert_labels"
    diff = "diff"
    text_file = "text_file"
    crash_info = "crash_info"
    image_pull_backoff_info = "image_pull_backoff_info"
    pending_pod_info = "pending_pod_info"


class Enrichment:
    # This is the actual enrichment data
    blocks: List[BaseBlock] = []
    # General purpose rendering flags, that can be used by specific sinks
    annotations: Dict[str, str] = {}
    enrichment_type: Optional[EnrichmentType]
    title: Optional[str]

    def __init__(
        self,
        blocks: List[BaseBlock],
        annotations: Optional[Dict[str, str]] = None,
        enrichment_type: Optional[EnrichmentType] = None,
        title: Optional[str] = None,
    ):
        if annotations is None:
            annotations = {}
        self.blocks = blocks
        self.annotations = annotations
        self.enrichment_type = enrichment_type
        self.title = title

    def __str__(self):
        return f"annotations: {self.annotations} Enrichment: {self.blocks} "


class FilterableScopeMatcher(BaseScopeMatcher):
    def __init__(self, data):
        self.data = data

    def get_data(self) -> Dict:
        return self.data

    def scope_match_namespace_labels(self, attr_matcher, attr_value):
        return self.match_labels_annotations(attr_matcher, attr_value)


class Filterable(ABC):
    @property
    @abstractmethod
    def attribute_map(self) -> Dict[str, Union[str, Dict[str, str]]]:
        raise NotImplementedError

    def get_invalid_attributes(self, attributes: List[str]) -> List:
        return list(set(attributes) - set(self.attribute_map))

    def attribute_matches(self, attribute: str, expression: Union[str, List[str], Dict, List[Dict]]) -> bool:
        value: Union[str, Dict[str, str]] = self.attribute_map[attribute]
        if isinstance(expression, str) or isinstance(expression, Dict):
            return Filterable.__value_match(value, expression)
        else:  # expression is list of values
            return any([Filterable.__value_match(value, single_exp) for single_exp in expression])

    @staticmethod
    def __value_match(value: Union[str, Dict[str, str]], expression: Union[str, Dict]) -> bool:
        if isinstance(value, str) and isinstance(expression, str):
            return bool(re.match(expression, value))
        elif isinstance(value, Dict) and isinstance(expression, Dict):  # value is Dict[str, str], expression is a Dict
            return expression.items() <= value.items()
        else:
            logging.error(f"Failed to evaluate matcher. Finding value: {value} matcher: {expression}")
            return False

    def matches(self, match_requirements: Dict[str, Union[str, List[str]]], scope_requirements) -> bool:
        # 1. "scope" check
        accept = True
        if scope_requirements is not None:
            data = self.attribute_map
            try:
                data["namespace_labels"] = get_namespace_labels(data["namespace"])
            except KeyError:
                data["namespace_labels"] = {}
            matcher = FilterableScopeMatcher(data)
            if scope_requirements.exclude:
                if matcher.scope_inc_exc_matches(scope_requirements.exclude):
                    return False
            if scope_requirements.include:
                if matcher.scope_inc_exc_matches(scope_requirements.include):
                    return True
                else:  # include was defined, but not matched. So if not matched by old matcher, should be rejected!
                    accept = False

        # 2. "match" check
        invalid_attributes = self.get_invalid_attributes(list(match_requirements.keys()))
        if len(invalid_attributes) > 0:
            logging.warning(f"Invalid match attributes: {invalid_attributes}")
            return False

        for attribute, expression in match_requirements.items():
            if not self.attribute_matches(attribute, expression):
                return False
        return accept


class FindingSubject:
    def __init__(
        self,
        name: str = None,
        subject_type: FindingSubjectType = FindingSubjectType.TYPE_NONE,
        namespace: str = None,
        node: str = None,
        container: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
        annotations: Optional[Dict[str, str]] = None,
    ):
        self.name = name
        self.subject_type = subject_type
        self.namespace = namespace
        self.node = node
        self.container = container
        self.labels = labels or {}
        self.annotations = annotations or {}

    def __str__(self):
        if self.namespace is not None:
            return f"{self.namespace}/{self.subject_type.value}/{self.name}"
        return f"{self.subject_type.value}/{self.name}"


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
        # TODO: this is bug-prone - see https://towardsdatascience.com/python-pitfall-mutable-default-arguments-9385e8265422
        subject: FindingSubject = FindingSubject(),
        finding_type: FindingType = FindingType.ISSUE,
        failure: bool = True,
        creation_date: str = None,
        fingerprint: str = None,
        starts_at: datetime = None,
        ends_at: datetime = None,
        add_silence_url: bool = False,
        silence_labels: Dict[Any, Any] = None,
    ) -> None:
        self.id: uuid.UUID = uuid.uuid4()
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
        self.video_links: List[VideoLink] = []
        self.service = TopServiceResolver.guess_cached_resource(name=subject.name, namespace=subject.namespace)
        self.service_key = self.service.get_resource_key() if self.service else ""
        uri_path = f"services/{self.service_key}?tab=grouped" if self.service_key else "graphs"
        self.investigate_uri = f"{ROBUSTA_UI_DOMAIN}/{uri_path}"
        self.add_silence_url = add_silence_url
        self.silence_labels = silence_labels
        self.creation_date = creation_date
        self.fingerprint = (
            fingerprint if fingerprint else self.__calculate_fingerprint(subject, source, aggregation_key)
        )
        self.starts_at = starts_at if starts_at else datetime.now()
        self.ends_at = ends_at
        self.dirty = False

    @property
    def attribute_map(self) -> Dict[str, Union[str, Dict[str, str]]]:
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
            "labels": self.subject.labels,
            "annotations": self.subject.annotations,
        }

    def _map_service_to_uri(self):
        if not self.service:
            return "graphs"
        if self.service.resource_type.lower() == "job":
            return "jobs"
        return "services"

    def get_investigate_uri(self, account_id: str, cluster_name: Optional[str] = None):
        uri_path = self._map_service_to_uri()
        kind = self.service.resource_type if self.service else None
        if kind and kind.lower() == "job":
            params = {
                "account": account_id,
                "cluster": f'"{cluster_name}"' if cluster_name else None,
                "namespace": f'"{self.subject.namespace}"' if self.subject.namespace else None,
                "name": f'"{self.service.name}"' if self.service else None,
            }
        else:
            params = {
                "account": account_id,
                "clusters": f'["{cluster_name}"]' if cluster_name else None,
                "namespaces": f'["{self.subject.namespace}"]' if self.subject.namespace else None,
                "kind": kind,
                "name": self.service.name if self.service else None,
                "names": f'["{self.aggregation_key}"]' if self.aggregation_key else None,
            }

        params = {k: v for k, v in params.items() if v is not None}
        uri_path = f"{uri_path}?{urlencode(params)}"
        return f"{ROBUSTA_UI_DOMAIN}/{uri_path}"

    def add_enrichment(
        self,
        enrichment_blocks: List[BaseBlock],
        annotations=None,
        suppress_warning: bool = False,
        enrichment_type: Optional[EnrichmentType] = None,
        title: Optional[str] = None,
    ):
        if self.dirty and not suppress_warning:
            logging.warning("Updating a finding after it was added to the event is not allowed!")

        if not enrichment_blocks:
            return
        if annotations is None:
            annotations = {}
        self.enrichments.append(
            Enrichment(blocks=enrichment_blocks, annotations=annotations, enrichment_type=enrichment_type, title=title)
        )

    def add_video_link(self, video_link: VideoLink, suppress_warning: bool = False):
        if self.dirty and not suppress_warning:
            logging.warning("Updating a finding after it was added to the event is not allowed!")

        self.video_links.append(video_link)

    def __str__(self):
        return f"title: {self.title} desc: {self.description} severity: {self.severity} sub-name: {self.subject.name} sub-type:{self.subject.subject_type.value} enrich: {self.enrichments}"

    def get_prometheus_silence_url(self, account_id: str, cluster_name: str) -> str:
        labels: Dict[str, str] = {"alertname": self.aggregation_key, "cluster": cluster_name, "account": account_id}
        kind: Optional[str] = self.subject.subject_type.value
        if kind == "node":
            pass
        else:
            if self.subject.namespace:
                labels["namespace"] = self.subject.namespace

            if self.silence_labels and self.silence_labels.get("service"):
                labels["service"] = self.silence_labels["service"]

            # In prometheus, job is related to the scrape target.
            # Kubernetes jobs are stored in job_name.
            if kind and self.subject.name:
                kind = "job_name" if kind == "job" else kind
                labels[kind] = self.subject.name

        labels["referer"] = "sink"
        # New label added here should be added to the UI silence create whitelist as well.
        return f"{ROBUSTA_UI_DOMAIN}/silences/create?{urllib.parse.urlencode(labels)}"

    @staticmethod
    def __calculate_fingerprint(subject: FindingSubject, source: FindingSource, aggregation_key: str) -> str:
        # some sinks require a unique fingerprint, typically used for two reasons:
        # 1. de-dupe the same alert if it fires twice
        # 2. update an existing alert and change its status from firing to resolved
        #
        # if we have a fingerprint available from the trigger (e.g. alertmanager) then use that
        # if not, generate with logic similar to alertmanager
        s = f"{subject.subject_type},{subject.name},{subject.namespace},{subject.node},{source.value}{aggregation_key}"
        return hashlib.sha256(s.encode()).hexdigest()
