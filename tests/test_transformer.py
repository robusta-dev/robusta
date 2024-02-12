from datetime import datetime
from unittest.mock import ANY, patch

import pytest
from hikaru import HikaruBase

from robusta.core.reporting.blocks import (
    DividerBlock,
    FileBlock,
    ListBlock,
    HeaderBlock,
    JsonBlock,
    KubernetesDiffBlock,
    LinkProp,
    LinksBlock,
    MarkdownBlock,
    ScanReportBlock,
    TableBlock,
)
from robusta.core.reporting.consts import ScanType
from robusta.core.sinks.transformer import Transformer


class TestTransformer:
    @pytest.fixture(params=[False, True])
    def transformer(self, request):
        return Transformer()

    @pytest.mark.parametrize(
        "block,expected_result",
        [
            (
                MarkdownBlock("hello world\nyeah  \ncool *beans*"),
                "<p>hello world\nyeah <br />\ncool <b>beans</b></p>\n",
            ),
            (DividerBlock(), "-------------------"),
            (JsonBlock('{"x":   [1,\n "y"] \t}'), '{"x":   [1,\n "y"] \t}'),
            # XXX as the example below shows, the JsonBlock class doesn't really validate
            # anything and basically implements an identity transform for arbitrary text
            # in block_to_html.
            (JsonBlock("not valid JSON"), "not valid JSON"),
            (
                KubernetesDiffBlock(
                    # We're abusing Hikaru internals here, but that seems to be the quickest
                    # way to create a semi-functional, non-trivial diff.
                    interesting_diffs=HikaruBase.get_empty_instance().diff(None),
                    old=None,
                    new=None,
                    name="abcd",
                    kind="Deployment"
                ),
                "<p><b></b>: None ==&gt; None</p>\n",
            ),
            (ListBlock(["hello", "world"]), "<p><b> hello\n</b> world</p>\n"),
            (HeaderBlock("HEADER"), "<strong>HEADER</strong>"),
            (
                TableBlock(rows=[[1, 2, "x"], ["p", 0, None]], headers=["h1", "h2", "h3"], table_name="table_name"),
                """<p>table_name</p>\n<table><thead><tr><th>h1  </th><th style="text-align: right;">  h2</th><th>h3  </th></tr></thead><tbody><tr><td>1   </td><td style="text-align: right;">   2</td><td>x   </td></tr><tr><td>p   </td><td style="text-align: right;">   0</td><td>    </td></tr></tbody></table>""",
            ),
        ],
    )
    def test_to_html(self, transformer, block, expected_result):
        assert transformer.block_to_html(block) == expected_result

    @pytest.mark.parametrize(
        "bad_block",
        [
            FileBlock(filename="x.png", contents=b"abcd"),
            LinksBlock(links=[LinkProp(text="a", url="a.com"), LinkProp(text="b", url="b.org")]),
            ScanReportBlock(
                title="title",
                scan_id="1234",
                type=ScanType.KRR,
                start_time=datetime(1945, 5, 11, 22, 43),
                end_time=datetime(1969, 6, 21, 20, 17),
                score="123",
                results=[],
                config="config",
            ),
        ],
    )
    def test_file_links_scan_report_blocks(self, transformer, bad_block):
        with patch("robusta.core.sinks.transformer.logging") as mock_logging:
            assert transformer.block_to_html(bad_block) == ""
        mock_logging.warning.assert_called_once_with(ANY)
