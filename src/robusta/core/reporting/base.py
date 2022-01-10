import uuid
from enum import Enum
from pydantic.main import BaseModel
from typing import List, Dict

from ..model.env_vars import ROBUSTA_UI_DOMAIN
from ..reporting.consts import FindingSubjectType, FindingSource, FindingType
from ...core.discovery.top_service_resolver import TopServiceResolver


class BaseBlock(BaseModel):
    hidden: bool = False


class FindingSeverity(Enum):
    INFO = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4


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


class FindingSubject:
    def __init__(
        self,
        name: str = None,
        subject_type: FindingSubjectType = FindingSubjectType.TYPE_NONE,
        namespace: str = None,
    ):
        self.name = name
        self.subject_type = subject_type
        self.namespace = namespace


class Finding:
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
            name=subject.name,
            namespace=subject.namespace
        )
        uri_path = f"services/{self.service_key}?tab=grouped" if self.service_key else "graphs"
        self.investigate_uri = f"{ROBUSTA_UI_DOMAIN}/{uri_path}"

    def add_enrichment(self, enrichment_blocks: List[BaseBlock], annotations=None):
        if not enrichment_blocks:
            return
        if annotations is None:
            annotations = {}
        self.enrichments.append(Enrichment(enrichment_blocks, annotations))

    def __str__(self):
        return f"title: {self.title} desc: {self.description} severity: {self.severity} sub-name: {self.subject.name} sub-type:{self.subject.subject_type.value} enrich: {self.enrichments}"
