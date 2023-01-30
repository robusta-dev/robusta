import logging
import re
from queue import PriorityQueue
from typing import Dict, List, Tuple, Union

from robusta.core.reporting import (
    BaseBlock,
    FileBlock,
    Finding,
    FindingSeverity,
    HeaderBlock,
    ListBlock,
    MarkdownBlock,
    TableBlock,
)
from robusta.core.reporting.utils import add_pngs_for_all_svgs
from robusta.core.sinks.jira.jira_sink_params import JiraSinkParams
from robusta.integrations.jira.client import JiraClient

SEVERITY_EMOJI_MAP = {
    FindingSeverity.HIGH: ":red_circle:",
    FindingSeverity.MEDIUM: ":large_orange_circle:",
    FindingSeverity.LOW: ":large_yellow_circle:",
    FindingSeverity.INFO: ":large_green_circle:",
}
SEVERITY_COLOR_MAP = {
    FindingSeverity.HIGH: "#d11818",
    FindingSeverity.MEDIUM: "#e48301",
    FindingSeverity.LOW: "#ffdc06",
    FindingSeverity.INFO: "#05aa01",
}

STRONG_MARK_REGEX = r"\*{1}[\w|\s\d%!><=\-:;@#$%^&()\.\,\]\[\\\/'\"]+\*{1}"
ITALIAN_MARK_REGEX = r"(^|\s+)_{1}[\w|\s\d%!*><=\-:;@#$%^&()\.\,\]\[\\\/'\"]+_{1}(\s+|$)"
CODE_REGEX = r"`{1,3}[\w|\s\d%!*><=\-:;@#$%^&()\.\,\]\[\\\/'\"]+`{1,3}"


def to_paragraph(txt, attrs=None):
    marks = {}
    if attrs:
        marks = {"marks": [*attrs]}
    return {"text": txt, "type": "text", **marks}


def _union_lists(*arrays):
    return [el for arr in arrays for el in arr]


def to_italian_text(txt, marks=None):
    marks = _union_lists((marks or []), [{"type": "em"}])
    return to_markdown_text(txt, ITALIAN_MARK_REGEX, marks, "_")


def to_code_text(txt, marks=None):
    marks = _union_lists((marks or []), [{"type": "code"}])
    return to_markdown_text(txt, CODE_REGEX, marks, "```")


def to_strong_text(txt, marks=None):
    marks = _union_lists((marks or []), [{"type": "strong"}])
    return to_markdown_text(txt, STRONG_MARK_REGEX, marks, "*")


def to_markdown_text(txt, regex, marks, replacement_char):
    return to_paragraph(re.sub(regex, lambda m: m.group(0).replace(replacement_char, ""), txt), marks)


MARKDOWN_MAPPER = {
    lambda x: re.search(STRONG_MARK_REGEX, x): {
        "split": lambda x: re.split(f"({STRONG_MARK_REGEX})", x),
        "replace": lambda x, marks=None: to_strong_text(x, marks),
    },
    lambda x: re.search(ITALIAN_MARK_REGEX, x): {
        "split": lambda x: re.split(f"({ITALIAN_MARK_REGEX})", x),
        "replace": lambda x, marks=None: to_italian_text(x, marks),
    },
    lambda x: re.search(CODE_REGEX, x): {
        "split": lambda x: re.split(f"({CODE_REGEX})", x),
        "replace": lambda x, marks=None: to_code_text(x, marks),
    },
}


class JiraSender:
    def __init__(self, cluster_name: str, account_id: str, params: JiraSinkParams):
        self.cluster_name = cluster_name
        self.account_id = account_id
        self.params = params
        print(self.params.dedups)
        logging.info(self.params.dedups)
        self.client = JiraClient(self.params)

    def _markdown_to_jira(self, text):
        # Using priority queue to determine which markdown to eject first. Bigger text -
        # bigger priority.
        pq = PriorityQueue()
        for condition in MARKDOWN_MAPPER.keys():
            search = condition(text)
            if search:
                # Priority queue puts the smallest number first, so we need to replace
                # start with beginning
                match_length = search.span()[0] - search.span()[1]
                pq.put_nowait((match_length, condition))

        text = [to_paragraph(text)]
        while not pq.empty():
            _, condition = pq.get_nowait()
            funcs = MARKDOWN_MAPPER[condition]
            func_split, func_replace = funcs["split"], funcs["replace"]
            i = 0
            while i < len(text):
                text_part = text[i]["text"]
                marks = text[i].get("marks", None)
                parts = func_split(text_part)
                new_parts = []
                for part in parts:
                    if not len(part):
                        continue
                    part = func_replace(part, marks) if condition(part) else to_paragraph(part, marks)
                    new_parts.append(part)
                text = text[:i] + new_parts + text[i + 1 :]
                i += len(new_parts)
        return text

    def __to_jira(self, block: BaseBlock, sink_name: str) -> List[Union[Dict[str, str], Tuple[str, bytes, str]]]:
        if isinstance(block, MarkdownBlock):
            if not block.text:
                return []
            return [{"type": "paragraph", "content": self._markdown_to_jira(block.text)}]
        elif isinstance(block, FileBlock):
            return [(block.filename, block.contents, "application/octet-stream")]
        elif isinstance(block, HeaderBlock):
            return self.__to_jira(MarkdownBlock(block.text), sink_name)
        elif isinstance(block, TableBlock):
            return [{"type": "codeBlock", "content": [{"text": block.to_markdown().text, "type": "text"}]}]
        elif isinstance(block, ListBlock):
            return [
                {
                    "type": "bulletList",
                    "content": [
                        {
                            "type": "listItem",
                            "content": [{"type": "paragraph", "content": [{"type": "text", "text": str(item)}]}],
                        }
                        for item in block.items
                    ],
                }
            ]
        else:
            logging.warning(f"cannot convert block of type {type(block)} to jira format block")
            return []  # no reason to crash the entire report

    def __parse_blocks_to_jira(self, report_blocks: List[BaseBlock]):
        # Process attachment blocks
        file_blocks = add_pngs_for_all_svgs([b for b in report_blocks if isinstance(b, FileBlock)])
        # Process attachment blocks
        other_blocks = [b for b in report_blocks if not isinstance(b, FileBlock)]

        if not self.params.send_svg:
            file_blocks = [b for b in file_blocks if not b.filename.endswith(".svg")]

        output_blocks = []
        for block in other_blocks:
            output_blocks.extend(self.__to_jira(block, self.params.name))

        output_file_blocks = []
        for block in file_blocks:
            output_file_blocks.extend(self.__to_jira(block, self.params.name))

        return output_blocks, output_file_blocks

    def send_finding_to_jira(
        self,
        finding: Finding,
        platform_enabled: bool,
    ):
        blocks: List[BaseBlock] = []
        actions = []

        if platform_enabled:  # add link to the robusta ui, if it's configured
            investigate_url = finding.get_investigate_uri(self.account_id, self.cluster_name)
            actions.append(to_paragraph("🔎 Investigate", [{"type": "link", "attrs": {"href": investigate_url}}]))
            if finding.add_silence_url:
                actions.append(
                    to_paragraph(
                        "🔕 Silence",
                        [
                            {
                                "type": "link",
                                "attrs": {
                                    "href": finding.get_prometheus_silence_url(self.account_id, self.cluster_name)
                                },
                            }
                        ],
                    )
                )

            for video_link in finding.video_links:
                actions.append(
                    to_paragraph(f"🎬 {video_link.name}", [{"type": "link", "attrs": {"href": video_link.url}}])
                )

        actions = [{"type": "paragraph", "content": actions}]
        # first add finding description block
        if finding.description:
            blocks.append(MarkdownBlock(finding.description))

        for enrichment in finding.enrichments:
            blocks.extend(enrichment.blocks)

        output_blocks, file_blocks = self.__parse_blocks_to_jira(blocks)
        logging.debug("Creating issue")
        labels = []
        for attr in self.params.dedups:
            if hasattr(finding, attr):
                labels.append(getattr(finding, attr))
            elif attr in finding.attribute_map:
                labels.append(finding.attribute_map[attr])
            elif attr == "cluster_name":
                labels.append(self.cluster_name)

        self.client.create_issue(
            {
                "description": {"type": "doc", "version": 1, "content": actions + output_blocks},
                "summary": finding.title,
                "labels": labels,
            },
            file_blocks,
        )
