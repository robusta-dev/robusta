# TODO: add a KubernetesBlock for rendering Kubernetes object in a standard way
# Notes on how we define all the classes below:
# 1. We use pydantic and not dataclasses so that field types are validated
# 2. We add __init__ methods ourselves for convenience. Without our own __init__ method, something like
#       HeaderBlock("foo") doesn't work. Only HeaderBlock(text="foo") would be allowed by pydantic.
import textwrap
import uuid
from copy import deepcopy
from typing import List, Callable, Dict, Any, Iterable, Sequence, Optional

import hikaru
from hikaru import DiffDetail, DiffType
from hikaru.model import HikaruDocumentBase
from pydantic import BaseModel
from tabulate import tabulate
from enum import Enum

from .custom_rendering import render_value
from ..reporting.consts import FindingSource, FindingSubjectType, FindingType

BLOCK_SIZE_LIMIT = 2997  # due to slack block size limit of 3000


class BaseBlock(BaseModel):
    hidden: bool = False


class MarkdownBlock(BaseBlock):
    text: str

    def __init__(self, text: str, single_paragraph: bool = False):
        if single_paragraph:
            text = textwrap.dedent(text)
            text = text.replace("\n", "")

        if len(text) >= BLOCK_SIZE_LIMIT:
            text = text[:BLOCK_SIZE_LIMIT] + "..."
        super().__init__(text=text)


class DividerBlock(BaseBlock):
    pass


class FileBlock(BaseBlock):
    filename: str
    contents: bytes

    def __init__(self, filename: str, contents: bytes):
        super().__init__(filename=filename, contents=contents)


class HeaderBlock(BaseBlock):
    text: str

    def __init__(self, text: str):
        super().__init__(text=text)


class ListBlock(BaseBlock):
    items: List[str]

    def __init__(self, items: List[str]):
        super().__init__(items=items)

    def to_markdown(self) -> MarkdownBlock:
        mrkdwn = [f"* {item}" for item in self.items]
        return MarkdownBlock("\n".join(mrkdwn))


# TODO: we should add a generalization of this which isn't K8s specific
class KubernetesDiffBlock(BaseBlock):
    diffs: List[DiffDetail]
    old: Optional[str]
    new: Optional[str]
    resource_name: Optional[str]
    num_additions: Optional[int]
    num_deletions: Optional[int]
    num_modifications: Optional[int]

    # note that interesting_diffs might be a subset of the full diff between old and new
    def __init__(
        self,
        interesting_diffs: List[DiffDetail],
        old: Optional[HikaruDocumentBase],
        new: Optional[HikaruDocumentBase],
    ):
        num_additions = len(
            [d for d in interesting_diffs if d.diff_type == DiffType.ADDED]
        )
        num_deletions = len(
            [d for d in interesting_diffs if d.diff_type == DiffType.REMOVED]
        )
        num_modifications = len(interesting_diffs) - num_additions - num_deletions

        super().__init__(
            diffs=interesting_diffs,
            old=self._obj_to_content(old),
            new=self._obj_to_content(new),
            resource_name=self._obj_to_name(old) or self._obj_to_name(new),
            num_additions=num_additions,
            num_deletions=num_deletions,
            num_modifications=num_modifications,
        )

    @staticmethod
    def _obj_to_content(obj: Optional[HikaruDocumentBase]):
        if obj is None:
            return ""
        else:
            return hikaru.get_yaml(obj)

    @staticmethod
    def _obj_to_name(obj: Optional[HikaruDocumentBase]):
        if obj is None:
            return ""
        if not hasattr(obj, "metadata"):
            return ""

        name = getattr(obj.metadata, "name", "")
        namespace = getattr(obj.metadata, "namespace", "")
        kind = getattr(obj, "kind", "").lower()
        return f"{kind}/{namespace}/{name}.yaml"


class JsonBlock(BaseBlock):
    json_str: str

    def __init__(self, json_str: str):
        super().__init__(json_str=json_str)


class TableBlock(BaseBlock):
    rows: List[List]
    headers: Sequence[str] = ()
    column_renderers: Dict = {}

    def __init__(
        self, rows: List[List], headers: Sequence[str] = (), column_renderers: Dict = {}
    ):
        super().__init__(rows=rows, headers=headers, column_renderers=column_renderers)

    def to_markdown(self) -> MarkdownBlock:
        # TODO: when the next version of tabulate is released, use maxcolwidths to wrap lines that are too long
        # this is currently implemented on tabulate's git master but isn't yet in the pypi package
        # unfortunately, we can't take a dependency on the tabulate git version as that breaks our package with pypi
        # see https://github.com/python-poetry/poetry/issues/2828
        table = tabulate(self.render_rows(), headers=self.headers, tablefmt="presto")
        return MarkdownBlock(f"```\n{table}\n```")

    def render_rows(self) -> List[List]:
        if self.column_renderers is None:
            return self.rows
        new_rows = deepcopy(self.rows)
        for (column_name, renderer_type) in self.column_renderers.items():
            column_idx = self.headers.index(column_name)
            for row in new_rows:
                row[column_idx] = render_value(renderer_type, row[column_idx])
        return new_rows


class KubernetesFieldsBlock(TableBlock):
    def __init__(
        self,
        k8s_obj: HikaruDocumentBase,
        fields: List[str],
        explanations: Dict[str, str] = {},
    ):
        """
        :param k8s_obj: a kubernetes object
        :param fields: a list of fields to display. for example ["metadata.name", "metadata.namespace"]
        :param explanations: an explanation for each field. for example {"metdata.name": "the pods name"}
        """
        if explanations:
            rows = [
                [f, k8s_obj.object_at_path(f.split(".")), explanations.get(f, "")]
                for f in fields
            ]
            super().__init__(rows=rows, headers=["field", "value", "explanation"])
        else:
            rows = [[f, k8s_obj.object_at_path(f.split("."))] for f in fields]
            super().__init__(rows=rows, headers=["field", "value"])


class CallbackBlock(BaseBlock):
    choices: Dict[str, Callable]
    context: Dict[str, Any] = {}

    def __init__(self, choices: Dict[str, Callable], context: Dict[str, Any]):
        super().__init__(choices=choices, context=context)


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
    def __init__(
        self,
        title: str,
        severity: FindingSeverity = FindingSeverity.INFO,
        source: FindingSource = FindingSource.NONE,
        aggregation_key: str = None,
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
