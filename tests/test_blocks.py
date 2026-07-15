import json

from hikaru.model.rel_1_26 import HikaruDocumentBase, ObjectMeta, Pod

from robusta.api import (  # LinkProp,; LinksBlock,
    CallbackBlock,
    CallbackChoice,
    DividerBlock,
    ExecutionBaseEvent,
    FileBlock,
    Finding,
    HeaderBlock,
    JsonBlock,
    KubernetesDiffBlock,
    ListBlock,
    MarkdownBlock,
    ScanReportRow,
    SlackSender,
    TableBlock,
    action,
)
from robusta.core.reporting.consts import ScanType
from robusta.core.sinks.slack.slack_sink_params import SlackSinkParams
from tests.config import CONFIG
from tests.utils.slack_utils import SlackChannel

TEST_ACCOUNT = "test account"
TEST_CLUSTER = "test cluster"
TEST_KEY = "test key"


def test_send_to_slack(slack_channel: SlackChannel):
    slack_sender = SlackSender(
        CONFIG.PYTEST_IN_CLUSTER_SLACK_TOKEN, TEST_ACCOUNT, TEST_CLUSTER, TEST_KEY, slack_channel.channel_name, registry=None
    )
    msg = "Test123"
    finding = Finding(title=msg, aggregation_key=msg)
    finding.add_enrichment([MarkdownBlock("testing")])
    slack_params = SlackSinkParams(name="test_slack", slack_channel=slack_channel.channel_name, api_key="")
    slack_sender.send_finding_to_slack(finding, slack_params, False)
    assert slack_channel.get_latest_message() == msg


# still not fully implemented, see commented out code
def create_finding_with_all_blocks():
    markdown_text = "*This is a markdown block*\n_This is a simple markdown block test_"
    markdown_block = MarkdownBlock(markdown_text)

    divider_block = DividerBlock()

    file_contents = b"This is a simple text file"
    file_block = FileBlock("sample.txt", file_contents)

    header_block = HeaderBlock("This is a header block")

    list_items = ["Item 1", "Item 2", "Item 3"]
    list_block = ListBlock(list_items)

    obj = Pod(metadata=ObjectMeta(name="theName", namespace="the-namespace"))
    obj2 = Pod(metadata=ObjectMeta(name="theName", namespace="the-namespace2"))
    diff_detail = obj.diff(obj2)
    kubernetes_diff_block = KubernetesDiffBlock(
        diff_detail, obj, obj2, "sample_kubernetes_diff_block", kind=obj.kind, namespace="default"
    )

    json_block = JsonBlock(json.dumps({"key": "value"}))

    table_rows = [["Row1_Col1", "Row1_Col2"], ["Row2_Col1", "Row2_Col2"]]
    table_block = TableBlock(table_rows, headers=["Header1", "Header2"])

    # kubernetes_fields_block = KubernetesFieldsBlock(HikaruDocumentBase(), ["field1", "field2"])
    @action
    def test_callback(event: ExecutionBaseEvent):
        print("Hello, World!")

    callback_choice = CallbackChoice(action=test_callback)
    callback_block = CallbackBlock({"button1": callback_choice})

    # link_prop = LinkProp("OpenAI", "https://www.openai.com/")
    # links_block = LinksBlock([link_prop])

    # prometheus_query_result = PrometheusQueryResult(resultType="vector", result=[])
    # prometheus_block = PrometheusBlock(prometheus_query_result, "sample_prometheus_query")

    scan_report_row = ScanReportRow(
        scan_id="1234",
        scan_type=ScanType.POPEYE,
        kind="Pod",
        name="sample_pod",
        namespace="default",
        container="sample_container",
        content=[],
        priority=1.0,
    )
    # scan_report_block = ScanReportBlock(
    #     title="Test Report",
    #     scan_id="1234",
    #     type=ScanType.POPEYE,
    #     start_time=datetime.now(),
    #     end_time=datetime.now(),
    #     score="1",
    #     results=[scan_report_row],
    #     config="sample_config",
    # )

    # Now that we have all the blocks, we add them to a finding
    finding = Finding(title="Sample Finding", aggregation_key="FooBar")  # TODO: support default
    finding.add_enrichment(
        [
            markdown_block,
            divider_block,
            file_block,
            header_block,
            list_block,
            kubernetes_diff_block,
            json_block,
            table_block,
            # kubernetes_fields_block,
            callback_block,
            # links_block,
            # prometheus_block,
            # scan_report_block,
        ]
    )
    return finding


def test_all_block_types(slack_channel: SlackChannel):
    slack_sender = SlackSender(
        CONFIG.PYTEST_IN_CLUSTER_SLACK_TOKEN, TEST_ACCOUNT, TEST_CLUSTER, TEST_KEY, slack_channel.channel_name,registry=None
    )
    slack_params = SlackSinkParams(name="test_slack", slack_channel=slack_channel.channel_name, api_key="")
    finding = create_finding_with_all_blocks()
    result = slack_sender.send_finding_to_slack(finding, slack_params, False)
    # result = slack_sender.send_finding_to_slack(finding, slack_params, True)
    print(result)


# Regression tests for FRO-211 / ROB-3946: the "Alerts Summary" digest table
# rendered a corrupted ASCII table because long cell values (Java class names in
# the label:site column) were word-wrapped onto extra physical lines instead of
# being truncated. These tests pin down that rows stay single-line and over-wide
# cells are truncated with an ellipsis.
LONG_CLASS_NAME = "ats.betting.betcatcher.settlement.settler.AbstractBetSettler"


def test_to_table_string_truncates_wide_column_without_wrapping():
    rows = [
        [LONG_CLASS_NAME, "103", "0"],
        ["orders.checkout.impl.OrderServiceImpl", "16", "4"],
    ]
    table_block = TableBlock(rows=rows, headers=["label:site", "Fired", "Resolved"])

    output = table_block.to_table_string(table_max_width=40)
    lines = output.splitlines()

    # presto renders: header line + separator line + exactly one line per row.
    # If any cell had wrapped, there would be extra physical lines here.
    assert len(lines) == 2 + len(rows)
    # Every physical line stays bounded: the content budget (table_max_width) plus
    # the fixed per-column separator/padding overhead tabulate adds. Without the
    # fix, wrapped cells would have blown past this and split rows across lines.
    assert all(len(line) <= 40 + 6 * len(table_block.headers) for line in lines)

    # The over-wide class name is truncated, not present in full, and the "wrap
    # spillover" fragments from the bug report never appear on their own line.
    assert LONG_CLASS_NAME not in output
    assert "…" in output
    assert not any(line.strip() in ("ServiceImpl", "erviceImpl") for line in lines)


def test_to_table_string_keeps_distinctive_suffix_of_dotted_names():
    table_block = TableBlock(rows=[[LONG_CLASS_NAME, "103", "0"]], headers=["label:site", "Fired", "Resolved"])

    output = table_block.to_table_string(table_max_width=40)

    # Dotted, space-free qualified names are trimmed from the left so the class
    # name (the distinctive suffix) survives.
    assert "AbstractBetSettler" in output
    assert "ats.betting.betcatcher" not in output


def test_to_table_string_never_truncates_numeric_columns():
    table_block = TableBlock(
        rows=[[LONG_CLASS_NAME, "103", "9999"]],
        headers=["label:site", "Fired", "Resolved"],
    )

    output = table_block.to_table_string(table_max_width=40)

    # The numeric counters are always shown in full - only the wide text column shrinks.
    assert "103" in output
    assert "9999" in output
    assert "…" not in output.split("103")[1]  # nothing after the counters got ellipsized


def test_to_table_string_trailing_truncation_for_plain_text():
    long_sentence = "this is a fairly long free text value that should be cut at the end"
    table_block = TableBlock(rows=[[long_sentence, "1", "0"]], headers=["message", "Fired", "Resolved"])

    output = table_block.to_table_string(table_max_width=30)

    # Plain text (contains spaces) is truncated from the right, ending in an ellipsis.
    assert "this is a fairly" in output
    assert "…" in output
    assert long_sentence not in output


def test_to_markdown_wide_table_stays_single_line_per_row():
    rows = [[LONG_CLASS_NAME, "103", "0"], ["orders.checkout.impl.OrderServiceImpl", "16", "4"]]
    table_block = TableBlock(rows=rows, headers=["label:site", "Fired", "Resolved"])

    markdown = table_block.to_markdown().text

    # Strip the ``` code fences, then assert the table body is header + separator + one line per row.
    inner = markdown.strip().strip("`").strip("\n")
    body_lines = [line for line in inner.splitlines() if line.strip()]
    assert len(body_lines) == 2 + len(rows)
