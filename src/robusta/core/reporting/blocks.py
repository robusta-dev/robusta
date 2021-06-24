# TODO: add a KubernetesBlock for rendering Kubernetes object in a standard way
# Notes on how we define all the classes below:
# 1. We use pydantic and not dataclasses so that field types are validated
# 2. We add __init__ methods ourselves for convenience. Without our own __init__ method, something like
#       HeaderBlock("foo") doesn't work. Only HeaderBlock(text="foo") would be allowed by pydantic.
from typing import List, Callable, Dict, Any, Iterable

from pydantic import BaseModel
from tabulate import tabulate


class BaseBlock (BaseModel):
    hidden: bool = False


class MarkdownBlock (BaseBlock):
    text: str

    def __init__(self, text: str):
        super().__init__(text=text)


class DividerBlock (BaseBlock):
    pass


class FileBlock (BaseBlock):
    filename: str
    contents: bytes

    def __init__(self, filename: str, contents: bytes):
        super().__init__(filename=filename, contents=contents)


class HeaderBlock (BaseBlock):
    text: str

    def __init__(self, text: str):
        super().__init__(text=text)


class ListBlock (BaseBlock):
    items: List[str]

    def __init__(self, items: List[str]):
        super().__init__(items=items)

    def to_markdown(self) -> MarkdownBlock:
        mrkdwn = [f"* {item}" for item in self.items]
        return MarkdownBlock("\n".join(mrkdwn))


class TableBlock (BaseBlock):
    rows: Iterable[Iterable[str]]
    headers: Iterable[str] = ()

    def __init__(self, rows: Iterable[Iterable[str]], headers: Iterable[str] = ()):
        super().__init__(rows=rows, headers=headers)

    def to_markdown(self) -> MarkdownBlock:
        table = tabulate(self.rows, headers=self.headers, tablefmt="presto")
        return MarkdownBlock(f"```\n{table}\n```")


class CallbackBlock (BaseBlock):
    choices: Dict[str, Callable]
    context: Dict[str, Any] = {}

    def __init__(self, choices: Dict[str, Callable], context: Dict[str, Any]):
        super().__init__(choices=choices, context=context)

