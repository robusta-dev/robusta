import json

from robusta.core.reporting import Finding
from robusta.core.reporting.blocks import MarkdownBlock, TableBlock
from robusta.integrations.msteams.msteams_elements.msteams_card import MsTeamsCard
from robusta.integrations.msteams.msteams_msg import MsTeamsMsg


def _card_len(msg: MsTeamsMsg) -> int:
    # same compact UTF-8 serialization the HTTP client sends
    return len(json.dumps(MsTeamsCard(msg.entire_msg).get_map_value(), ensure_ascii=True).encode("utf-8"))


def _add_title(msg: MsTeamsMsg):
    finding = Finding(title="title", aggregation_key="key", description="short description")
    msg.write_title_and_desc(False, finding, "cluster", "account")


def test_large_message_body_is_truncated_to_fit_budget():
    msg = MsTeamsMsg(webhook_url="http://example.com", prefer_redirect_to_platform=False)
    _add_title(msg)
    for i in range(20):
        msg.markdown_block(MarkdownBlock(f"block-{i} " + "a" * 2900))
    msg.write_current_section()

    complete_card_map = MsTeamsCard(msg.entire_msg).get_map_value()
    assert _card_len(msg) > MsTeamsMsg.MAX_SIZE_IN_BYTES

    msg._trim_card_body_up_to_max_limit(complete_card_map)

    assert _card_len(msg) <= MsTeamsMsg.MAX_SIZE_IN_BYTES


def test_small_message_is_not_modified():
    msg = MsTeamsMsg(webhook_url="http://example.com", prefer_redirect_to_platform=False)
    _add_title(msg)
    msg.markdown_block(MarkdownBlock("small block"))
    msg.write_current_section()

    complete_card_map = MsTeamsCard(msg.entire_msg).get_map_value()
    before = _card_len(msg)
    assert before <= MsTeamsMsg.MAX_SIZE_IN_BYTES

    msg._trim_card_body_up_to_max_limit(complete_card_map)
    assert _card_len(msg) == before


def test_table_rows_are_trimmed_to_fit_budget():
    msg = MsTeamsMsg(webhook_url="http://example.com", prefer_redirect_to_platform=False)
    rows = [[f"cell-{i}" * 100 for _ in range(4)] for i in range(300)]
    msg.table(TableBlock(rows=rows, headers=["a", "b", "c", "d"], table_name="events"))
    msg.write_current_section()

    complete_card_map = MsTeamsCard(msg.entire_msg).get_map_value()
    assert _card_len(msg) > MsTeamsMsg.MAX_SIZE_IN_BYTES

    msg._trim_card_body_up_to_max_limit(complete_card_map)

    assert _card_len(msg) <= MsTeamsMsg.MAX_SIZE_IN_BYTES


def test_table_trim_stops_when_budget_is_met():
    # Boundary case: payload exceeds the limit by less than one row's serialized
    # size (including the JSON array separator). Removing exactly one row must
    # stop the loop instead of dropping an extra row.
    msg = MsTeamsMsg(webhook_url="http://example.com", prefer_redirect_to_platform=False)
    _add_title(msg)

    filler_rows = [[f"small-{i}" for _ in range(2)] for i in range(30)]
    msg.table(TableBlock(rows=filler_rows, headers=["a", "b"], table_name="filler"))
    msg.write_current_section()

    table = TableBlock(
        rows=[["big-row", "x" * 600] for _ in range(40)],
        headers=["a", "b"],
        table_name="events",
    )
    msg.table(table)
    msg.write_current_section()

    complete_card_map = MsTeamsCard(msg.entire_msg).get_map_value()
    assert _card_len(msg) > MsTeamsMsg.MAX_SIZE_IN_BYTES

    msg._trim_card_body_up_to_max_limit(complete_card_map)

    assert _card_len(msg) <= MsTeamsMsg.MAX_SIZE_IN_BYTES

    # trimming walks from the end of the message, so the earlier "filler"
    # table must be untouched once the budget is met on the "events" table
    body = complete_card_map["attachments"][0]["content"]["body"]
    tables = [element["rows"] for element in body if element.get("type") == "Table"]
    assert len(tables) == 2
    filler_rows_after, events_rows_after = tables
    assert len(filler_rows_after) == 31  # 30 rows + header, untouched
    assert 1 <= len(events_rows_after) < 41  # header + at least one row kept


def test_escaped_and_non_ascii_text_is_trimmed_to_fit_serialized_bytes():
    # JSON escaping ("\n" -> "\\n") and non-ASCII UTF-8 encoding inflate the
    # serialized payload beyond the character count, which used to push the
    # final request over the Teams webhook limit.
    msg = MsTeamsMsg(webhook_url="http://example.com", prefer_redirect_to_platform=False)
    _add_title(msg)
    for i in range(20):
        msg.markdown_block(MarkdownBlock(f"block-{i} \n" + "Ω" * 2900))
    msg.write_current_section()

    complete_card_map = MsTeamsCard(msg.entire_msg).get_map_value()
    assert _card_len(msg) > MsTeamsMsg.MAX_SIZE_IN_BYTES

    msg._trim_card_body_up_to_max_limit(complete_card_map)
    assert _card_len(msg) <= MsTeamsMsg.MAX_SIZE_IN_BYTES

    # _card_len uses the same compact UTF-8 serialization the HTTP client sends,
    # so the assertion above already matches the actual request body.
    assert _card_len(msg) == len(json.dumps(complete_card_map, ensure_ascii=True).encode("utf-8"))
