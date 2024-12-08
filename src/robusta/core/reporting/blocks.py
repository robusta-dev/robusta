# TODO: add a KubernetesBlock for rendering Kubernetes object in a standard way
# Notes on how we define all the classes below:
# 1. We use pydantic and not dataclasses so that field types are validated
# 2. We add __init__ methods ourselves for convenience. Without our own __init__ method, something like
#       HeaderBlock("foo") doesn't work. Only HeaderBlock(text="foo") would be allowed by pydantic.
import gzip
import itertools
import json
import logging
import textwrap
from copy import deepcopy
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Literal, Optional, Sequence, Tuple, Union

import hikaru
from hikaru import DiffDetail, DiffType
from hikaru.model.rel_1_26 import HikaruDocumentBase
from pydantic import BaseModel

from robusta.core.model.base_params import ChartValuesFormat

try:
    from tabulate import tabulate
except ImportError:

    def tabulate(*args, **kwargs):
        raise ImportError("Please install tabulate to use the TableBlock")


from prometrix import PrometheusQueryResult

from robusta.core.model.env_vars import PRINTED_TABLE_MAX_WIDTH
from robusta.core.model.pods import format_unit
from robusta.core.reporting.base import BaseBlock
from robusta.core.reporting.consts import ScanType
from robusta.core.reporting.custom_rendering import render_value

BLOCK_SIZE_LIMIT = 2997  # due to slack block size limit of 3000


class MarkdownBlock(BaseBlock):
    """
    A Block of `Markdown <https://en.wikipedia.org/wiki/Markdown>`__
    """

    text: str

    def __init__(self, text: str, dedent: bool = False):
        """
        :param text: one or more paragraphs of Markdown markup
        :param dedent: if True, remove common indentation so that you can use multi-line docstrings.
        """
        if dedent:
            if text[0] == "\n":
                text = text[1:]
            text = textwrap.dedent(text)

        if len(text) >= BLOCK_SIZE_LIMIT:
            text = text[:BLOCK_SIZE_LIMIT] + "..."
        super().__init__(text=text)


class DividerBlock(BaseBlock):
    """
    A visual separator between other blocks
    """

    pass


class FileBlock(BaseBlock):
    """
    A file of any type. Used for images, log files, binary files, and more.
    """

    filename: str
    contents: bytes

    def __init__(
        self,
        filename: str,
        contents: bytes,
        **kwargs,
    ):
        """
        :param filename: the file's name
        :param contents: the file's contents
        """
        super().__init__(
            filename=filename,
            contents=contents,
            **kwargs,
        )

    def is_text_file(self):
        return self.filename.endswith((".txt", ".log"))

    def zip(self):
        try:
            self.contents = gzip.compress(self.contents)
            self.filename = self.filename + ".gz"
        except Exception as exc:
            logging.error(f"Unexpected error occurred while zipping file {self.filename}")
            logging.exception(exc)

    def truncate_content(self, max_file_size_bytes: int) -> bytes:
        """
        Truncates the log file by removing lines from the beginning until its size is within the given limit.
        """
        # we don't want to truncate other files like images
        if not self.is_text_file():
            return self.contents

        decoded_content = self.contents.decode("utf-8")
        content_length = len(decoded_content)

        if content_length <= max_file_size_bytes:
            return self.contents

        lines = decoded_content.splitlines()
        byte_length_newline = len("\n".encode("utf-8"))

        truncated_lines: List[str] = []
        for idx, line in enumerate(lines):
            line_content_length = len(line) + byte_length_newline

            content_length -= line_content_length
            if content_length <= max_file_size_bytes:
                truncated_lines = lines[idx + 1 :]
                break

        return "\n".join(truncated_lines).encode("utf-8")


class EmptyFileBlock(BaseBlock):
    """
    Handle empty log files
    """

    metadata: dict = {}
    filename: str

    def __init__(
        self,
        filename: str,
        remarks: str,
        metadata: Optional[dict] = None,
        **kwargs,
    ):
        """
        :param filename: the file's name
        :param contents: the file's contents
        """
        super().__init__(
            filename=filename,
            metadata=metadata or {},
            **kwargs,
        )

        self.metadata["is_empty"] = True
        self.metadata["remarks"] = remarks


class HeaderBlock(BaseBlock):
    """
    Text formatted as a header
    """

    text: str

    def __init__(self, text: str):
        """
        :param text: the header
        """
        super().__init__(text=text)


class ListBlock(BaseBlock):
    """
    A list of items, nicely formatted
    """

    items: List[str]

    def __init__(self, items: List[str]):
        """
        :param items: a list of strings
        """
        super().__init__(items=items)

    def to_markdown(self) -> MarkdownBlock:
        mrkdwn = [f"* {item}" for item in self.items]
        return MarkdownBlock("\n".join(mrkdwn))


# TODO: we should add a generalization of this which isn't K8s specific
class KubernetesDiffBlock(BaseBlock):
    """
    A diff between two versions of a Kubernetes object
    """

    diffs: List[DiffDetail]
    old: Optional[str]
    new: Optional[str]
    old_obj: Optional[HikaruDocumentBase]
    new_obj: Optional[HikaruDocumentBase]
    resource_name: Optional[str]
    num_additions: Optional[int]
    num_deletions: Optional[int]
    num_modifications: Optional[int]
    kind: str

    # note that interesting_diffs might be a subset of the full diff between old and new
    def __init__(
        self,
        interesting_diffs: List[DiffDetail],
        old: Optional[HikaruDocumentBase],
        new: Optional[HikaruDocumentBase],
        name: str,
        kind: str,
        namespace: str = None,
    ):
        """
        :param interesting_diffs: parts of the diff to emphasize - some sinks will only show these to save space
        :param old: the old version of the object
        :param new: the new version of the object
        """
        num_additions = len([d for d in interesting_diffs if d.diff_type == DiffType.ADDED])
        num_deletions = len([d for d in interesting_diffs if d.diff_type == DiffType.REMOVED])
        num_modifications = len(interesting_diffs) - num_additions - num_deletions

        resource_name = self._obj_to_name(old, name, namespace) or self._obj_to_name(new, name, namespace)

        super().__init__(
            diffs=interesting_diffs,
            old=self._obj_to_content(old),
            new=self._obj_to_content(new),
            old_obj=old,
            new_obj=new,
            resource_name=resource_name,
            num_additions=num_additions,
            num_deletions=num_deletions,
            num_modifications=num_modifications,
            kind=kind,
        )

    def get_description(self):
        if not self.old:
            return f"{self.kind} created"
        elif not self.new:
            return f"{self.kind} deleted"
        else:
            return self.__updated_description()

    def __updated_description(self):
        length = 5
        updated_fields = []
        for diff in self.diffs:
            if diff.path:
                # Stripping any integer values like '0', '1', '2', etc. from the path array which denotes array
                # indices. eg: ['spec', 'template', 'spec', 'containers', '0', 'image']
                stripped_path = [path for path in diff.path if not path.isdigit()]
                if stripped_path:
                    updated_fields.append(stripped_path[-1])

        updated_fields_str = ""
        if updated_fields:
            updated_fields_str = f"\n ● Attributes: "

            updated_fields_len = len(updated_fields)
            if updated_fields_len < length:
                updated_fields_str += f"{', '.join(updated_fields)}"
            else:
                updated_fields_str += (
                    f"{', '.join(updated_fields[:length])} ... (and {updated_fields_len - length} more)"
                )

        return f"{self.kind} updated{updated_fields_str}"

    @staticmethod
    def _obj_to_content(obj: Optional[HikaruDocumentBase]):
        if obj is None:
            return ""
        else:
            return hikaru.get_yaml(obj)

    @staticmethod
    def _obj_to_name(obj: Optional[HikaruDocumentBase], name: str, namespace: str = ""):
        if obj is None:
            return ""

        kind = getattr(obj, "kind", "").lower()
        obj_name = ""
        if kind:
            obj_name += f"{kind}/"
        if namespace:
            obj_name += f"{namespace}/"

        return f"{obj_name}{name}.yaml"


class JsonBlock(BaseBlock):
    """
    Json data
    """

    json_str: str

    def __init__(self, json_str: str):
        """
        :param json_str: json as a string
        """
        super().__init__(json_str=json_str)


class TableBlockFormat(Enum):
    vertical: str = "vertical"


class TableBlock(BaseBlock):
    """
    Table display of a list of lists.

    Note: Wider tables appears as a file attachment on Slack, because they aren't rendered properly inline

    :var column_width: Hint to sink for the portion of size each column should use. Not supported by all sinks.
        example: [1, 1, 1, 2] use twice the size for last column.
    """

    rows: List[List]
    headers: Sequence[str] = ()
    column_renderers: Dict = {}
    table_name: str = ""
    column_width: List[int] = None
    metadata: Dict[str, Any] = {}
    table_format: Optional[TableBlockFormat] = None

    def __init__(
        self,
        rows: List[List],
        headers: Sequence[str] = (),
        column_renderers: Dict = {},
        table_name: str = "",
        column_width: List[int] = None,
        metadata: Dict[str, Any] = {},
        table_format: Optional[TableBlockFormat] = None,
        **kwargs,
    ):
        """
        :param rows: a list of rows. each row is a list of columns
        :param headers: names of each column
        """
        super().__init__(
            rows=rows,
            headers=headers,
            column_renderers=column_renderers,
            table_name=table_name,
            column_width=column_width,
            metadata=metadata,
            **kwargs,
        )

        if table_format:
            self.metadata["format"] = TableBlockFormat.vertical.value

    @classmethod
    def __calc_max_width(cls, headers, rendered_rows, table_max_width: int) -> List[int]:
        # We need to make sure the total table width, doesn't exceed the max width,
        # otherwise, the table is printed corrupted
        columns_max_widths = [len(header) for header in headers]
        for row in rendered_rows:
            for idx, val in enumerate(row):
                columns_max_widths[idx] = max(len(str(val)), columns_max_widths[idx])

        if sum(columns_max_widths) > table_max_width:  # We want to limit the widest column
            largest_width = max(columns_max_widths)
            widest_column_idx = columns_max_widths.index(largest_width)
            diff = sum(columns_max_widths) - table_max_width
            columns_max_widths[widest_column_idx] = largest_width - diff
            if columns_max_widths[widest_column_idx] < 0:  # in case the diff is bigger than the largest column
                # just divide equally
                columns_max_widths = [
                    int(table_max_width / len(columns_max_widths)) for i in range(0, len(columns_max_widths))
                ]

        return columns_max_widths

    @classmethod
    def __trim_rows(cls, contents: str, max_chars: int):
        # We need to make sure that the total character count doesn't exceed max_chars,
        # but if we cut off a row in the middle then it messes up the whole table.
        # So instead remove entire rows at a time
        if len(contents) <= max_chars:
            return contents

        truncator = "\n..."
        max_chars -= len(truncator)

        lines = contents.splitlines()
        length_so_far = 0
        lines_to_include = 0
        for line in lines:
            new_length = length_so_far + len("\n") + len(line)
            if new_length > max_chars:
                break
            else:
                length_so_far = new_length
                lines_to_include += 1

        return "\n".join(lines[:lines_to_include]) + truncator

    @classmethod
    def __to_strings_rows(cls, rows):
        # This is just to assert all row column values are strings. Tabulate might fail on other types
        return [list(map(lambda column_value: str(column_value), row)) for row in rows]

    def to_markdown(self, max_chars=None, add_table_header: bool = True) -> MarkdownBlock:
        table_header = f"{self.table_name}\n" if self.table_name else ""
        table_header = "" if not add_table_header else table_header
        prefix = f"{table_header}```\n"
        suffix = "\n```"
        table_contents = self.to_table_string()
        if max_chars is not None:
            max_chars = max_chars - len(prefix) - len(suffix)
            table_contents = self.__trim_rows(table_contents, max_chars)

        return MarkdownBlock(f"{prefix}{table_contents}{suffix}")

    def to_table_string(self, table_max_width: int = PRINTED_TABLE_MAX_WIDTH, table_fmt: str = "presto") -> str:
        rendered_rows = self.__to_strings_rows(self.render_rows())
        col_max_width = self.__calc_max_width(self.headers, rendered_rows, table_max_width)
        return tabulate(
            rendered_rows,
            headers=self.headers,
            tablefmt=table_fmt,
            maxcolwidths=col_max_width,
        )

    def render_rows(self) -> List[List]:
        if self.column_renderers is None:
            return self.rows
        new_rows = deepcopy(self.rows)
        for column_name, renderer_type in self.column_renderers.items():
            column_idx = self.headers.index(column_name)
            for row in new_rows:
                row[column_idx] = render_value(renderer_type, row[column_idx])
        return new_rows


class KubernetesFieldsBlock(TableBlock):
    """
    A nicely formatted Kubernetes objects, with a subset of the fields shown
    """

    def __init__(
        self,
        k8s_obj: HikaruDocumentBase,
        fields: List[str],
        explanations: Dict[str, str] = {},
    ):
        """
        :param k8s_obj: a kubernetes object
        :param fields: a list of fields to display. for example ["metadata.name", "metadata.namespace"]
        :param explanations: an explanation for each field. for example {"metadata.name": "the pods name"}
        """
        if explanations:
            rows = [[f, k8s_obj.object_at_path(f.split(".")), explanations.get(f, "")] for f in fields]
            super().__init__(rows=rows, headers=["field", "value", "explanation"])
        else:
            rows = [[f, k8s_obj.object_at_path(f.split("."))] for f in fields]
            super().__init__(rows=rows, headers=["field", "value"])


class CallbackChoice(BaseModel):
    action: Callable
    action_params: Optional[BaseModel]
    kubernetes_object: Optional[Any]

    class Config:
        arbitrary_types_allowed = True


class CallbackBlock(BaseBlock):
    """
    A set of buttons that allows callbacks from the sink - for example, a button in Slack that will trigger another action when clicked
    """

    choices: Dict[str, CallbackChoice]

    def __init__(self, choices: Dict[str, CallbackChoice]):
        """
        :param choices: a dict mapping between each the text on each button to the action it triggers
        """
        super().__init__(choices=choices)


class LinkProp(BaseModel):
    text: str
    url: str


class LinksBlock(BaseBlock):
    """
    A set of links
    """

    links: List[LinkProp] = []


class PrometheusBlockLineData(BaseBlock):
    legend: str
    value: Any


class PrometheusBlock(BaseBlock):
    """
    Formatted prometheus query results with metadata
    """

    data: PrometheusQueryResult
    metadata: Dict[str, str]
    vertical_lines: Optional[List[PrometheusBlockLineData]]
    horizontal_lines: Optional[List[PrometheusBlockLineData]]
    y_axis_type: Optional[ChartValuesFormat]
    graph_name: Optional[str]

    class Config:
        arbitrary_types_allowed = True

    def __init__(
        self,
        data: PrometheusQueryResult,
        query: str,
        vertical_lines: Optional[List[PrometheusBlockLineData]] = None,
        horizontal_lines: Optional[List[PrometheusBlockLineData]] = None,
        y_axis_type: Optional[ChartValuesFormat] = None,
        graph_name: Optional[str] = None,
        metrics_legends_labels: Optional[List[str]] = None,
    ):
        """
        :param data: the PrometheusQueryResult generated created from a prometheus query
        :param query: the Prometheus query run
        """
        metadata = {"query-result-version": "1.0", "query": query}
        super().__init__(
            data=data,
            metadata=metadata,
            vertical_lines=vertical_lines,
            horizontal_lines=horizontal_lines,
            y_axis_type=y_axis_type,
            graph_name=graph_name,
        )

        if metrics_legends_labels:
            self.metadata["metrics_legends_labels"] = json.dumps(metrics_legends_labels)

    def dict(self, *args, **kwargs) -> Dict[str, Any]:
        obj_dict = super().dict()
        obj_dict["y_axis_type"] = str(self.y_axis_type) if self.y_axis_type else None

        return obj_dict


class ScanReportRow(BaseModel):
    scan_id: str  # UUID
    scan_type: ScanType
    kind: Optional[str]
    name: Optional[str]
    namespace: Optional[str]
    container: Optional[str]
    content: List[Any]  # scan result data
    priority: float


TableRow = Tuple[str, ...]
ScanTable = Dict[str, List[TableRow]]


class ScanReportBlock(BaseBlock):
    title: str
    scan_id: str  # UUID
    type: ScanType
    start_time: datetime
    end_time: datetime
    score: str
    results: List[ScanReportRow]
    config: str
    metadata: Dict[str, Any] = {}

    @property
    def grade(self):
        score = int(self.score)
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        elif score >= 50:
            return "E"
        else:
            return "F"

    @property
    def table_headers(self) -> List[str]:
        raise NotImplementedError("table_headers property must be implemented in the subclass")

    @property
    def table_data(self) -> ScanTable:
        raise NotImplementedError("table_data property must be implemented in the subclass")

    @property
    def table_widths(self) -> Tuple[int, ...]:
        raise NotImplementedError("table_widths property must be implemented in the subclass")


class PopeyeScanReportBlock(ScanReportBlock):
    @property
    def table_headers(self) -> List[str]:
        return ["Priority", "Namespace", "Name", "Container", "Issues"]

    @property
    def table_widths(self) -> Tuple[int, ...]:
        return (10, 25, 25, 25, 65)

    @property
    def table_data(self) -> ScanTable:
        sorted_data = sorted(self.results, key=lambda x: x.kind or "", reverse=True)
        groupped_data = itertools.groupby(sorted_data, key=lambda x: x.kind)
        return {
            kind
            or "": [
                (
                    self.level_to_string(row.priority),
                    row.name or "",
                    row.namespace or "",
                    row.container or "",
                    self.scan_row_content_format(row),
                )
                for row in rows
            ]
            for kind, rows in groupped_data
        }

    @staticmethod
    def level_to_string(level: Union[int, float]) -> str:
        level = int(level)

        if level == 1:
            return "Info"
        elif level == 2:
            return "Warning"
        elif level == 3:
            return "**Error**"
        else:
            return "OK"

    def scan_row_content_format(self, row: ScanReportRow) -> str:
        return "\n".join(f"{self.level_to_string(i['level'])} {i['message']}" for i in row.content)


class KRRScanReportBlock(ScanReportBlock):
    @property
    def table_headers(self) -> List[str]:
        return [
            "Priority",
            "Namespace",
            "Name",
            "Container",
            "CPU Request",
            "CPU Limit",
            "Memory Request",
            "Memory Limit",
        ]

    @property
    def table_widths(self) -> Tuple[int, ...]:
        return (5, 10, 10, 10, 8, 8, 8, 8)

    @staticmethod
    def __format_krr_value(value: Union[float, Literal["?"], None]) -> str:
        if value is None:
            return "unset"
        elif isinstance(value, str):
            return "?"
        else:
            return format_unit(value)

    @staticmethod
    def __format_content_str(allocated: float, recommended: float, info: Optional[str]) -> str:
        if allocated is None and recommended is None:
            return "unset"

        res = f"{KRRScanReportBlock.__format_krr_value(allocated)} -> {KRRScanReportBlock.__format_krr_value(recommended)}"
        if info is not None:
            res += f"\n({info})"
        return res

    @staticmethod
    def __parse_content(content) -> Tuple[str, ...]:
        content_by_resource = {row["resource"]: row for row in content}
        res = []

        for resource in ["cpu", "memory"]:
            for field in ["request", "limit"]:
                row = content_by_resource.get(resource)
                if not row:
                    # NOTE: We should always have a row for each resource,
                    # but if for some reason this is not true, add some value not to break the table
                    res.append("?")
                    continue

                allocated = row.get("allocated", {}).get(field, "?")
                recommended = row.get("recommended", {}).get(field, "?")
                info = row.get("info")

                res.append(KRRScanReportBlock.__format_content_str(allocated, recommended, info))

        return tuple(res)

    @property
    def table_data(self) -> ScanTable:
        sorted_data = sorted(self.results, key=lambda x: x.kind or "", reverse=True)
        groupped_data = itertools.groupby(sorted_data, key=lambda x: x.kind)
        return {
            kind
            or "": [
                (
                    self.__priority_to_severity(row.priority),
                    row.namespace or "",
                    row.name or "",
                    row.container or "",
                    *self.__parse_content(row.content),
                )
                for row in rows
            ]
            for kind, rows in groupped_data
        }

    @staticmethod
    def __priority_to_severity(priority: Union[int, float]) -> str:
        priority = int(priority)

        if priority == 4:
            return "**CRITICAL**"
        elif priority == 3:
            return "WARNING"
        elif priority == 2:
            return "OK"
        elif priority == 1:
            return "GOOD"
        else:
            return "UNKNOWN"


class EventRow(BaseModel):
    type: Optional[str]
    reason: Optional[str]
    message: Optional[str]
    kind: str
    name: str
    namespace: Optional[str]
    time: Optional[str]


class EventsBlock(TableBlock):
    """
    Table display of a Events, Persists the events on the Robusta Platform.

    Note: Wider tables appears as a file attachment on Slack, because they aren't rendered properly inline
    """

    events: List[EventRow] = []

    def __init__(
        self,
        events: List[EventRow],
        rows: List[List],
        headers: Sequence[str] = (),
        column_renderers: Dict = {},
        table_name: str = "",
        column_width: List[int] = None,
    ):
        """
        :param rows: a list of rows. each row is a list of columns
        :param headers: names of each column
        """
        super().__init__(
            events=events,
            rows=rows,
            headers=headers,
            column_renderers=column_renderers,
            table_name=table_name,
            column_width=column_width,
        )


class EventsRef(BaseBlock):
    namespace: Optional[str]
    name: str
    kind: str


class GraphBlock(FileBlock):
    graph_data: Optional[PrometheusBlock]

    def __init__(
        self,
        filename: str,
        contents: bytes,
        graph_data: Optional[PrometheusBlock] = None,
        **kwargs,
    ):
        super().__init__(
            filename=filename,
            contents=contents,
            graph_data=graph_data,
            **kwargs,
        )
