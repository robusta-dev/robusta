# TODO: add a KubernetesBlock for rendering Kubernetes object in a standard way
# Notes on how we define all the classes below:
# 1. We use pydantic and not dataclasses so that field types are validated
# 2. We add __init__ methods ourselves for convenience. Without our own __init__ method, something like
#       HeaderBlock("foo") doesn't work. Only HeaderBlock(text="foo") would be allowed by pydantic.
import textwrap
from copy import deepcopy
from typing import List, Callable, Dict, Any, Iterable, Sequence, Optional

import hikaru
from hikaru import DiffDetail, DiffType
from hikaru.model import HikaruDocumentBase
from pydantic import BaseModel
from tabulate import tabulate

from .custom_rendering import render_value
from .base import BaseBlock
from ..model.env_vars import PRINTED_TABLE_MAX_WIDTH

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

    def __init__(self, filename: str, contents: bytes):
        """
        :param filename: the file's name
        :param contents: the file's contents
        """
        super().__init__(filename=filename, contents=contents)


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
        """
        :param interesting_diffs: parts of the diff to emphasize - some sinks will only show these to save space
        :param old: the old version of the object
        :param new: the new version of the object
        """
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
    """
    Json data
    """

    json_str: str

    def __init__(self, json_str: str):
        """
        :param json_str: json as a string
        """
        super().__init__(json_str=json_str)


class TableBlock(BaseBlock):
    """
    Table display of a list of lists.
    """

    rows: List[List]
    headers: Sequence[str] = ()
    column_renderers: Dict = {}

    def __init__(
        self, rows: List[List], headers: Sequence[str] = (), column_renderers: Dict = {}
    ):
        """
        :param rows: a list of rows. each row is a list of columns
        :param headers: names of each column
        """
        super().__init__(rows=rows, headers=headers, column_renderers=column_renderers)

    @classmethod
    def __calc_max_width(cls, headers, rendered_rows) -> List[int]:
        # We need to make sure the total table width, doesn't exceed the max width,
        # otherwise, the table is printed corrupted
        columns_max_widths = [len(header) for header in headers]
        for row in rendered_rows:
            for idx, val in enumerate(row):
                columns_max_widths[idx] = max(len(str(val)), columns_max_widths[idx])

        if (
            sum(columns_max_widths) > PRINTED_TABLE_MAX_WIDTH
        ):  # We want to limit the widest column
            largest_width = max(columns_max_widths)
            widest_column_idx = columns_max_widths.index(largest_width)
            diff = sum(columns_max_widths) - PRINTED_TABLE_MAX_WIDTH
            columns_max_widths[widest_column_idx] = largest_width - diff
            if (
                columns_max_widths[widest_column_idx] < 0
            ):  # in case the diff is bigger than the largest column
                # just divide equally
                columns_max_widths = [
                    int(PRINTED_TABLE_MAX_WIDTH / len(columns_max_widths))
                    for i in range(0, len(columns_max_widths))
                ]

        return columns_max_widths

    @classmethod
    def __to_strings_rows(cls, rows):
        # This is just to assert all row column values are strings. Tabulate might fail on other types
        return [list(map(lambda column_value: str(column_value), row)) for row in rows]

    def to_markdown(self) -> MarkdownBlock:
        return MarkdownBlock(f"```\n{self.to_table_string()}\n```")

    def to_table_string(self) -> str:
        rendered_rows = self.__to_strings_rows(self.render_rows())
        col_max_width = self.__calc_max_width(self.headers, rendered_rows)
        return tabulate(
            rendered_rows,
            headers=self.headers,
            tablefmt="presto",
            maxcolwidths=col_max_width,
        )

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
