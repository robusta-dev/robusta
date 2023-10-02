from robusta.core.reporting.base import Enrichment
from robusta.core.reporting.blocks import HeaderBlock, MarkdownBlock
from robusta.core.sinks.opsgenie.opsgenie_sink import OpsGenieSink


class TestOpsGenieSink:
    def test___enrichments_as_text(self):
        enrichments = [
            Enrichment(blocks=[HeaderBlock("header"), MarkdownBlock("a")]),
            Enrichment(blocks=[MarkdownBlock("*b*")]),
        ]
        assert (
            OpsGenieSink._OpsGenieSink__enrichments_as_text(enrichments)
            == "<strong>header</strong>\n<p>a</p>\n---\n<p><b>b</b></p>\n"
        )
