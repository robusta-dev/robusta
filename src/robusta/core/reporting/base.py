import uuid
from enum import Enum
from pydantic.main import BaseModel
from typing import List, Dict

from ..reporting.consts import FindingSubjectType, FindingSource, FindingType


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
    """A Finding is an event that users should be aware of. For example, Findings are created for alerts,
    important configuration changes, and anything else playbooks want to tell users about.

    All results that playbooks want to show the user should be wrapped in a finding. You should never directly send
    messages to the user on Slack or in other manners.

     Args:
         arg1 (int): Description of arg1
         arg2 (str): Description of arg2

     Returns:
         bool: Description of return value

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

    def add_enrichment(self, enrichment_blocks: List[BaseBlock], annotations=None):
        if not enrichment_blocks:
            return
        if annotations is None:
            annotations = {}
        self.enrichments.append(Enrichment(enrichment_blocks, annotations))

    def __str__(self):
        return f"title: {self.title} desc: {self.description} severity: {self.severity} sub-name: {self.subject.name} sub-type:{self.subject.subject_type.value} enrich: {self.enrichments}"
