import json
import os
from datetime import datetime

import pytest
from hikaru import DiffDetail, DiffType
from hikaru.model.rel_1_26 import HikaruDocumentBase, ObjectMeta, Pod
from prometrix import PrometheusQueryResult

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
    KubernetesFieldsBlock,
    ListBlock,
    MarkdownBlock,
    PrometheusBlock,
    ScanReportBlock,
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
    slack_sender = SlackSender(CONFIG.PYTEST_IN_CLUSTER_SLACK_TOKEN, TEST_ACCOUNT, TEST_CLUSTER, TEST_KEY)
    msg = "test123"
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
    kubernetes_diff_block = KubernetesDiffBlock(diff_detail, obj, obj2,
                                                "sample_kubernetes_diff_block", kind=obj.kind, namespace="default")

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
    scan_report_block = ScanReportBlock(
        title="Test Report",
        scan_id="1234",
        type=ScanType.POPEYE,
        start_time=datetime.now(),
        end_time=datetime.now(),
        score="1",
        results=[scan_report_row],
        config="sample_config",
    )

    # Now that we have all the blocks, we add them to a finding
    finding = Finding(title="Sample Finding", aggregation_key="foo-bar")  # TODO: support default
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
    slack_sender = SlackSender(CONFIG.PYTEST_IN_CLUSTER_SLACK_TOKEN, TEST_ACCOUNT, TEST_CLUSTER, TEST_KEY)
    slack_params = SlackSinkParams(name="test_slack", slack_channel=slack_channel.channel_name, api_key="")
    finding = create_finding_with_all_blocks()
    result = slack_sender.send_finding_to_slack(finding, slack_params, False)
    # result = slack_sender.send_finding_to_slack(finding, slack_params, True)
    print(result)
