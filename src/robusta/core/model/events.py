import copy
import logging
import uuid
from collections import defaultdict
from enum import Enum
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field

from pydantic import BaseModel

from ..reporting import FindingSubjectType, FindingSource
from ...integrations.scheduled.playbook_scheduler import PlaybooksScheduler
from ..reporting.base import Finding, BaseBlock, FindingSeverity, FindingSubject, VideoLink


class EventType(Enum):
    KUBERNETES_TOPOLOGY_CHANGE = 1
    PROMETHEUS = 2
    MANUAL_TRIGGER = 3
    SCHEDULED_TRIGGER = 4


class ExecutionEventBaseParams(BaseModel):
    named_sinks: Optional[List[str]] = None


class ExecutionContext(BaseModel):
    account_id: str
    cluster_name: str


# Right now:
# 1. this is a dataclass but we need to make all fields optional in subclasses because of https://stackoverflow.com/questions/51575931/
# 2. this can't be a pydantic BaseModel because of various pydantic bugs (see https://github.com/samuelcolvin/pydantic/pull/2557)
# once the pydantic PR that addresses those issues is merged, this should be a pydantic class
# (note that we need to integrate with dataclasses because of hikaru)
@dataclass
class ExecutionBaseEvent:
    # Collection of findings that should be sent to each sink.
    # This collection is shared between different playbooks that are triggered by the same event.
    sink_findings: Dict[str, List[Finding]] = field(
        default_factory=lambda: defaultdict(list)
    )
    # Target sinks for this execution event. Each playbook may have a different list of target sinks.
    named_sinks: Optional[List[str]] = None
    response: Dict[
        str, Any
    ] = None  # Response returned to caller. For admission or manual triggers for example
    stop_processing: bool = False
    _scheduler: Optional[PlaybooksScheduler] = None
    _context: Optional[ExecutionContext] = None

    def set_context(self, context: ExecutionContext):
        self._context = context

    def get_context(self) -> ExecutionContext:
        return self._context

    def set_scheduler(self, scheduler: PlaybooksScheduler):
        self._scheduler = scheduler

    def get_scheduler(self) -> PlaybooksScheduler:
        return self._scheduler

    def create_default_finding(self) -> Finding:
        """Create finding default fields according to the event type"""
        return Finding(
            title="Robusta notification", aggregation_key="Generic finding key"
        )

    def __prepare_sinks_findings(self):
        finding_id: uuid = uuid.uuid4()
        for sink in self.named_sinks:
            if len(self.sink_findings[sink]) == 0:
                sink_finding = self.create_default_finding()
                sink_finding.id = (
                    finding_id  # share the same finding id between different sinks
                )
                self.sink_findings[sink].append(sink_finding)

    def add_video_link(
            self,
            video_link: VideoLink
    ):
        self.__prepare_sinks_findings()
        for sink in self.named_sinks:
            self.sink_findings[sink][0].add_video_link(video_link, True)

    def add_enrichment(
        self,
        enrichment_blocks: List[BaseBlock],
        annotations=None,
    ):
        self.__prepare_sinks_findings()
        for sink in self.named_sinks:
            self.sink_findings[sink][0].add_enrichment(enrichment_blocks, annotations, True)

    def add_finding(self, finding: Finding, suppress_warning: bool = False):
        finding.dirty = True  # Warn if new enrichments are added to this finding directly
        first = True  # no need to clone the finding on the first sink. Use the orig finding
        for sink in self.named_sinks:
            if (len(self.sink_findings[sink]) > 0) and not suppress_warning:
                logging.warning(
                    f"Overriding active finding for {sink}. new finding: {finding}"
                )
            if not first:
                finding = copy.deepcopy(finding)
            self.sink_findings[sink].insert(0, finding)
            first = False

    def override_finding_attributes(self, title: str = "", description: str = "", severity: FindingSeverity = None):
        for sink in self.named_sinks:
            for finding in self.sink_findings[sink]:
                if title:
                    finding.title = title
                if description:
                    finding.description = description
                if severity:
                    finding.severity = severity

    @staticmethod
    def from_params(params: ExecutionEventBaseParams) -> Optional["ExecutionBaseEvent"]:
        return ExecutionBaseEvent(named_sinks=params.named_sinks)

    def get_subject(self) -> FindingSubject:
        return FindingSubject(
            name="Unresolved",
            subject_type=FindingSubjectType.TYPE_NONE
        )

    @classmethod
    def get_source(cls) -> FindingSource:
        return FindingSource.NONE

