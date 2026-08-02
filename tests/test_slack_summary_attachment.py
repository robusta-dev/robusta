"""Tests for the file attachment on the Slack "Alerts Summary" digest (ROB-3946 / FRO-211).

The digest can only show part of a large table, so the complete one is attached as a file.
Slack files are immutable while the message is rewritten on every notification, so these tests
pin down the upload/refresh/delete lifecycle.
"""
import time
from unittest.mock import MagicMock, patch

import pytest

from robusta.core.sinks.sink_base import NotificationSummary
from robusta.core.sinks.slack.slack_sink_params import SlackSinkParams

SUMMARY_HEADER = ["label:site", "label:component"]
GROUP_HEADER = ["cluster: prod-nj1"]


@pytest.fixture
def slack():
    """A SlackSender wired to a mock Slack client, plus the recorded uploads/deletes."""
    with patch("robusta.integrations.slack.sender.WebClient") as web_client:
        from robusta.integrations.slack.sender import SlackSender

        client = MagicMock()
        uploads, deletes = [], []

        def upload(**kwargs):
            uploads.append(kwargs)
            return {"file": {"permalink": f"https://files.slack.com/f{len(uploads)}", "id": f"F{len(uploads)}"}}

        client.files_upload_v2.side_effect = upload
        client.files_delete.side_effect = lambda **kwargs: deletes.append(kwargs["file"])
        client.chat_postMessage.return_value = {"ts": "111.1", "channel": "C1"}
        client.chat_update.return_value = {"ts": "111.1", "channel": "C1"}
        web_client.return_value = client

        sender = SlackSender("xoxb-test", "account", "prod-nj1", "key", "chan", registry=None)
        # A file can only be shared once the channel id is known; posting a message records it.
        sender.channel_name_to_id["chan"] = "C1"
        yield sender, client, uploads, deletes


def _table(n_groups):
    return {
        (f"ats.betting.betcatcher.validation.impl.Validator{i:03d}Foo", "nj"): [i % 7, i % 3]
        for i in range(n_groups)
    }


def _send(sender, summary_table, state, **kwargs):
    return sender.send_or_update_summary_message(
        GROUP_HEADER,
        SUMMARY_HEADER,
        summary_table,
        SlackSinkParams(name="test", slack_channel="chan", api_key=""),
        False,
        time.time(),
        False,
        grouping_interval=86400,
        channel="chan",
        summary_state=state,
        **kwargs,
    )


def test_no_attachment_when_the_table_fits(slack):
    sender, client, uploads, _ = slack

    _send(sender, _table(1), NotificationSummary())

    assert uploads == []  # nothing was dropped, so there is nothing to attach
    assert "files.slack.com" not in str(client.chat_postMessage.call_args.kwargs["blocks"])


def test_attaches_the_full_table_when_rows_are_dropped(slack):
    sender, client, uploads, _ = slack
    state = NotificationSummary()

    _send(sender, _table(200), state)

    assert len(uploads) == 1
    assert state.attachment_permalink and state.attachment_file_id
    # Every group is in the file, even though the message only shows a fraction of them.
    assert uploads[0]["content"].decode().count("Validator") == 200
    # Without a channel the file is only linkable, not readable by anyone else.
    assert uploads[0]["channel"] == "C1"

    kwargs = client.chat_postMessage.call_args.kwargs
    assert any("files.slack.com" in str(block) for block in kwargs["blocks"])
    # Slack only shares an uploaded file if it is referenced from the message text too.
    assert "files.slack.com" in kwargs["text"]


def test_attachment_is_throttled_across_updates(slack):
    sender, _, uploads, _ = slack
    state = NotificationSummary()

    _send(sender, _table(200), state)
    sender.channel_name_to_id["chan"] = "C1"
    _send(sender, _table(200), state, msg_ts="111.1")

    assert len(uploads) == 1  # the message is rewritten per notification, the file is not


def test_refreshing_the_attachment_deletes_the_previous_file(slack):
    sender, _, uploads, deletes = slack
    state = NotificationSummary()

    _send(sender, _table(200), state)
    state.attachment_ts = 0  # pretend the throttle window elapsed
    sender.channel_name_to_id["chan"] = "C1"
    _send(sender, _table(200), state, msg_ts="111.1")

    assert len(uploads) == 2
    assert deletes == ["F1"]


def test_previous_interval_attachment_is_never_deleted(slack):
    # Each interval posts its own summary message, and that message keeps linking its own file
    # forever. Deleting it when the next interval starts would leave the older message pointing
    # at a file that no longer exists.
    sender, _, _, deletes = slack
    state = NotificationSummary()
    _send(sender, _table(200), state)

    state.start_ts = time.time() - 999999  # force the interval to expire
    state.register_notification(("x", "y"), False, 86400)
    assert state.attachment_file_id is None
    assert state.attachment_permalink is None

    _send(sender, _table(200), state)
    assert deletes == []  # the previous interval's file is left alone


def test_superseded_file_is_deleted_only_after_the_message_points_at_the_new_one(slack):
    sender, client, uploads, deletes = slack
    state = NotificationSummary()
    _send(sender, _table(200), state)
    state.attachment_ts = 0  # pretend the throttle window elapsed
    sender.channel_name_to_id["chan"] = "C1"

    # If updating the message fails, the message still links the old file, so it must survive.
    client.chat_update.side_effect = Exception("slack is down")
    _send(sender, _table(200), state, msg_ts="111.1")
    assert len(uploads) == 2
    assert deletes == [], "deleted a file the live message still points at"

    # Once an update succeeds, the superseded file can go.
    client.chat_update.side_effect = None
    state.attachment_ts = 0
    _send(sender, _table(200), state, msg_ts="111.1")
    assert deletes == ["F2"]


def test_upload_failure_does_not_break_the_summary(slack):
    sender, client, _, _ = slack
    client.files_upload_v2.side_effect = Exception("no files:write scope")

    ts = _send(sender, _table(200), NotificationSummary())

    assert ts == "111.1"  # the digest is still posted, just without the attachment
    assert "files.slack.com" not in str(client.chat_postMessage.call_args.kwargs["blocks"])


def test_summary_keys_mixing_none_and_strings_do_not_crash(slack):
    # Group keys hold raw attribute values - "workload" is None when a finding has no service -
    # and None is not comparable with str, so sorting must normalise before comparing.
    sender, client, _, _ = slack
    summary_table = {
        ("ats.wallet.DefaultFundsAdjuster", "nj"): [5, 2],
        (None, "nj"): [5, 2],  # same counts, so the tie-break has to compare the keys
    }

    ts = _send(sender, summary_table, NotificationSummary())

    assert ts == "111.1"
    assert "None" in str(client.chat_postMessage.call_args.kwargs["blocks"])


def test_non_threaded_summary_can_be_updated(slack):
    # A summary-only sink sends nothing else, so posting the summary has to record the channel
    # id itself - otherwise every update bails and a brand new summary is posted each time.
    sender, client, _, _ = slack
    sender.channel_name_to_id.clear()
    state = NotificationSummary()

    ts = _send(sender, _table(3), state)
    assert sender.channel_name_to_id["chan"] == "C1"

    assert _send(sender, _table(3), state, msg_ts=ts) == "111.1"
    assert client.chat_update.called


def test_attachment_is_skipped_until_the_channel_id_is_known(slack):
    # Sharing the file needs the channel id, which is only recorded once a message has been
    # posted. Rather than upload an unreadable file, the attachment waits for the next update.
    sender, _, uploads, _ = slack
    sender.channel_name_to_id.clear()

    _send(sender, _table(200), NotificationSummary())
    assert uploads == []
