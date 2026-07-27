import json
import re

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
from robusta.core.reporting.blocks import BLOCK_SIZE_LIMIT
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


# Regression tests for FRO-211 / ROB-3946: long values must stay complete (wrapped
# onto extra lines, never cut mid-value), and an over-long table must drop whole rows
# with a note rather than blow past Slack's block limit and lose its closing ``` fence.
LONG_CLASS_NAME = "ats.betting.betcatcher.settlement.settler.AbstractBetSettler"


def _column_values(output, column_index=0):
    """Rebuild each logical row's column value from a wrapped presto table."""
    values, lines = [], output.splitlines()
    for line in lines[2:]:  # skip header + separator
        if "|" not in line:
            continue
        cell = line.split("|")[column_index].strip()
        starts_new_row = all(part.strip() for part in line.split("|")[1:])
        if starts_new_row:
            values.append(cell)
        elif values:
            values[-1] += cell  # continuation of the previous row's wrapped value
    return values


def test_long_values_are_wrapped_not_cut():
    rows = [[LONG_CLASS_NAME, "103", "0"], ["orders.checkout.impl.OrderServiceImpl", "16", "4"]]
    table_block = TableBlock(rows=rows, headers=["label:site", "Fired", "Resolved"])

    output = table_block.to_table_string(table_max_width=40)

    # The full path survives, reassembled across the wrapped lines - nothing is elided.
    assert _column_values(output) == [LONG_CLASS_NAME, "orders.checkout.impl.OrderServiceImpl"]
    assert "…" not in output


def test_numeric_columns_are_not_shrunk():
    table_block = TableBlock(
        rows=[[LONG_CLASS_NAME, "103", "9999"]], headers=["label:site", "Fired", "Resolved"]
    )

    output = table_block.to_table_string(table_max_width=40)

    # Counters stay on one line - only the wide text column absorbs the reduction.
    assert "103" in output and "9999" in output
    assert all(line.count("|") == 2 for line in output.splitlines() if "|" in line)


def test_all_numeric_table_is_not_shrunk():
    values = ["123456789012345", "678901234567890", "112233445566778"]
    table_block = TableBlock(rows=[values], headers=["a", "b", "c"])

    output = table_block.to_table_string(table_max_width=10)

    for value in values:
        assert value in output


def test_headerless_and_ragged_rows():
    # No headers, and rows wider than the (empty) header list must not IndexError.
    table_block = TableBlock(rows=[[LONG_CLASS_NAME, "extra", "cols"]], headers=[])

    assert table_block.to_table_string(table_max_width=30)


def test_to_markdown_small_table_has_no_omission_note():
    table_block = TableBlock(rows=[[LONG_CLASS_NAME, "1", "0"]], headers=["label:site", "Fired", "Resolved"])

    markdown = table_block.to_markdown().text

    assert "more rows not shown" not in markdown
    assert markdown.startswith("```") and markdown.endswith("```")


def test_to_markdown_drops_whole_rows_and_keeps_code_fence():
    # The 4-column shape of the "Alerts Summary" digest that triggered the bug.
    rows = [[f"ats.betting.betcatcher.validation.impl.Validator{i:03d}Foo", "nj", "1", "0"] for i in range(200)]
    table_block = TableBlock(rows=rows, headers=["label:site", "label:component", "Fired", "Resolved"])

    markdown = table_block.to_markdown().text

    # Small enough that MarkdownBlock never blind-cuts it, so the fence is intact.
    assert len(markdown) < BLOCK_SIZE_LIMIT
    assert markdown.startswith("```") and markdown.endswith("```")
    # The reader is told what was left out.
    assert re.search(r"\.\.\. \d+ more rows not shown", markdown)

    # Every displayed value is a complete class name - rows are dropped as whole units,
    # so no row is left showing only the first half of a wrapped value.
    inner = markdown.split("```")[1]
    displayed = _column_values(inner)
    assert displayed  # some rows did survive
    for value in displayed:
        assert re.fullmatch(r"ats\.betting\.betcatcher\.validation\.impl\.Validator\d{3}Foo", value), value


def test_to_markdown_custom_omission_note_receives_dropped_rows():
    rows = [[f"ats.betting.betcatcher.validation.impl.Validator{i:03d}Foo", "nj", "1", "2"] for i in range(200)]
    table_block = TableBlock(rows=rows, headers=["label:site", "label:component", "Fired", "Resolved"])

    def omission_note(omitted):
        return f"... {len(omitted)} more groups ({sum(int(r[-2]) for r in omitted)} fired) not shown"

    markdown = table_block.to_markdown(omission_note=omission_note).text

    # The note reports the residual totals, so the table still reconciles with the header count.
    match = re.search(r"\.\.\. (\d+) more groups \((\d+) fired\) not shown", markdown)
    assert match, markdown[-200:]
    omitted_count, omitted_fired = int(match.group(1)), int(match.group(2))
    assert omitted_fired == omitted_count  # one "fired" per dropped row
    assert len(markdown) < BLOCK_SIZE_LIMIT
