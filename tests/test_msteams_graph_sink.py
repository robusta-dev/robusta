import json
from unittest.mock import ANY, MagicMock, patch

import pytest

from robusta.core.reporting import (
    Enrichment,
    FileBlock,
    Finding,
    FindingSeverity,
    FindingSource,
    FindingSubject,
    MarkdownBlock,
    TableBlock,
)
from robusta.core.reporting.base import FindingSubjectType
from robusta.core.sinks.msteams_graph.msteams_graph_sink import MsTeamsGraphSink
from robusta.core.sinks.msteams_graph.msteams_graph_sink_params import MsTeamsGraphSinkParams
from robusta.integrations.msteams.graph.graph_client import (
    SIGN_IN_FAILURE_BACKOFF_SEC,
    MsTeamsGraphClient,
    MsTeamsGraphError,
)
from robusta.integrations.msteams.graph.graph_msg import MsTeamsGraphMsg
from robusta.integrations.msteams.graph.sender import MsTeamsGraphSender

TEAM = "11111111-1111-1111-1111-111111111111"
OTHER_TEAM = "22222222-2222-2222-2222-222222222222"
DEFAULT_CHANNEL = "19:default@thread.tacv2"
TEAM_A_CHANNEL = "19:team-a@thread.tacv2"
NS_CHANNEL = "19:namespace@thread.tacv2"


def make_params(**overrides) -> MsTeamsGraphSinkParams:
    values = dict(
        name="teams_graph",
        tenant_id="tenant",
        client_id="client",
        username="robusta@example.onmicrosoft.com",
        password="secret",
        team_id=TEAM,
        channel_id=DEFAULT_CHANNEL,
    )
    values.update(overrides)
    return MsTeamsGraphSinkParams(**values)


def make_sink(params: MsTeamsGraphSinkParams) -> MsTeamsGraphSink:
    sink = MsTeamsGraphSink.__new__(MsTeamsGraphSink)
    sink.params = params
    sink.cluster_name = "test-cluster"
    sink.sender = MagicMock()
    return sink


def make_finding(namespace="payments", labels=None, annotations=None) -> Finding:
    return Finding(
        title="KubePodCrashLooping",
        aggregation_key="KubePodCrashLooping",
        severity=FindingSeverity.HIGH,
        source=FindingSource.PROMETHEUS,
        description="Pod payments/api is crash looping",
        subject=FindingSubject(
            name="api",
            subject_type=FindingSubjectType.TYPE_POD,
            namespace=namespace,
            labels=labels or {},
            annotations=annotations or {},
        ),
    )


NAMESPACE_METADATA = "robusta.core.sinks.common.destination_override._get_namespace_metadata"


@pytest.mark.parametrize(
    "params, labels, annotations, ns_annotations, expected",
    [
        # no overrides
        (make_params(), {}, {}, {}, (TEAM, DEFAULT_CHANNEL)),
        # subject label / annotation routing, same as Slack's channel_override
        (make_params(channel_override="labels.teams_channel"), {"teams_channel": TEAM_A_CHANNEL}, {}, {},
         (TEAM, TEAM_A_CHANNEL)),
        (make_params(channel_override="${annotations.example.com/teams-channel}"), {},
         {"example.com/teams-channel": TEAM_A_CHANNEL}, {}, (TEAM, TEAM_A_CHANNEL)),
        # override with another team
        (make_params(channel_override="labels.teams_channel"), {"teams_channel": f"{OTHER_TEAM}/{TEAM_A_CHANNEL}"},
         {}, {}, (OTHER_TEAM, TEAM_A_CHANNEL)),
        # namespace annotation wins over the subject label
        (make_params(namespace_channel_override="${annotations.example.com/teams-channel}",
                     channel_override="labels.teams_channel"),
         {"teams_channel": TEAM_A_CHANNEL}, {}, {"example.com/teams-channel": NS_CHANNEL},
         (TEAM, NS_CHANNEL)),
        # namespace annotation missing, fall back to the subject label
        (make_params(namespace_channel_override="${annotations.example.com/teams-channel}",
                     channel_override="labels.teams_channel"),
         {"teams_channel": TEAM_A_CHANNEL}, {}, {}, (TEAM, TEAM_A_CHANNEL)),
        # nothing resolved, send to the default channel
        (make_params(channel_override="labels.teams_channel"), {}, {}, {}, (TEAM, DEFAULT_CHANNEL)),
        # nothing resolved, drop
        (make_params(namespace_channel_override="${annotations.example.com/teams-channel}",
                     send_to_default_if_missing=False), {}, {}, {}, None),
    ],
)
def test_resolve_destination(params, labels, annotations, ns_annotations, expected):
    sink = make_sink(params)
    with patch(NAMESPACE_METADATA, return_value=({}, ns_annotations)):
        assert sink._resolve_destination(make_finding(labels=labels, annotations=annotations)) == expected


def test_dropped_finding_is_not_sent():
    sink = make_sink(make_params(channel_override="labels.teams_channel", send_to_default_if_missing=False))
    sink.write_finding(make_finding(), platform_enabled=False)
    sink.sender.send_finding.assert_not_called()


def test_disable_platform_links():
    sink = make_sink(make_params(disable_platform_links=True))
    sink.write_finding(make_finding(), platform_enabled=True)
    sink.sender.send_finding.assert_called_once()
    assert sink.sender.send_finding.call_args.args[1] is False


def test_scoped_namespace_only_config_loads():
    # oauth_scope must not shadow the sink scope (include/exclude) of SinkBaseParams
    params = make_params(
        namespace_channel_override="${annotations.example.com/teams-channel}",
        send_to_default_if_missing=False,
        scope={"include": [{"labels": "openshift_io_alert_source=platform"}, {"labels": "cluster=prod-cluster"}]},
        oauth_scope="https://graph.microsoft.com/ChannelMessage.Send",
    )
    assert params.scope.include is not None
    assert params.oauth_scope == "https://graph.microsoft.com/ChannelMessage.Send"


def test_invalid_override_is_rejected():
    with pytest.raises(ValueError):
        make_params(channel_override="not-a-template")


def ok_response(status_code=201, body=None):
    response = MagicMock()
    response.status_code = status_code
    response.ok = status_code < 400
    response.json.return_value = body or {}
    response.text = json.dumps(body or {})
    return response


def token_response():
    return ok_response(200, {"access_token": "token", "expires_in": 3600})


@patch("robusta.integrations.msteams.graph.graph_client.requests.post")
def test_client_ropc_token_is_cached_and_channel_id_is_encoded(post):
    post.side_effect = [token_response(), ok_response(), ok_response()]
    client = MsTeamsGraphClient("tenant", "client", "user@example.com", "pw", client_secret="cs")

    client.post_channel_message(TEAM, "19%3Aabc%40thread.tacv2", {"body": {}})
    client.post_channel_message(TEAM, "19:abc@thread.tacv2", {"body": {}})

    token_call, first_post, second_post = post.call_args_list
    assert token_call.args[0] == "https://login.microsoftonline.com/tenant/oauth2/v2.0/token"
    assert token_call.kwargs["data"]["grant_type"] == "password"
    assert token_call.kwargs["data"]["client_secret"] == "cs"
    assert token_call.kwargs["data"]["scope"] == "https://graph.microsoft.com/.default"
    expected_url = f"https://graph.microsoft.com/v1.0/teams/{TEAM}/channels/19%3Aabc%40thread.tacv2/messages"
    assert first_post.args[0] == expected_url
    assert second_post.args[0] == expected_url
    assert first_post.kwargs["headers"]["Authorization"] == "Bearer token"


@patch("robusta.integrations.msteams.graph.graph_client.requests.post")
def test_client_refreshes_token_on_401(post):
    post.side_effect = [token_response(), ok_response(401), token_response(), ok_response()]
    client = MsTeamsGraphClient("tenant", "client", "user@example.com", "pw")

    assert client.post_channel_message(TEAM, DEFAULT_CHANNEL, {}).ok
    assert post.call_count == 4


@patch("robusta.integrations.msteams.graph.graph_client.time.time")
@patch("robusta.integrations.msteams.graph.graph_client.requests.post")
def test_client_backs_off_after_failed_sign_in(post, now):
    post.side_effect = [ok_response(400, {"error": "invalid_grant", "error_description": "bad password"}),
                        token_response(), ok_response()]
    client = MsTeamsGraphClient("tenant", "client", "user@example.com", "wrong")

    now.return_value = 1000
    with pytest.raises(MsTeamsGraphError, match="bad password"):
        client.post_channel_message(TEAM, DEFAULT_CHANNEL, {})
    # alerts during the backoff don't hit the token endpoint again
    now.return_value = 1000 + SIGN_IN_FAILURE_BACKOFF_SEC - 1
    with pytest.raises(MsTeamsGraphError, match="failed recently"):
        client.post_channel_message(TEAM, DEFAULT_CHANNEL, {})
    assert post.call_count == 1

    now.return_value = 1000 + SIGN_IN_FAILURE_BACKOFF_SEC
    assert client.post_channel_message(TEAM, DEFAULT_CHANNEL, {}).ok
    assert post.call_count == 3


def finding_with_blocks() -> Finding:
    finding = make_finding()
    finding.add_enrichment(
        [
            MarkdownBlock("*Crash info*"),
            TableBlock([["api", "OOMKilled"]], ["container", "reason"]),
            FileBlock("api.log", b"line 1\nline 2\n"),
            FileBlock("graph.png", b"\x89PNG fake"),
        ]
    )
    return finding


def test_graph_message_shape():
    msg = MsTeamsGraphMsg(prefer_redirect_to_platform=False)
    finding = finding_with_blocks()
    msg.write_title_and_desc(True, finding, "test-cluster", "account")
    msg.write_enrichments(finding.enrichments, send_files=True)
    message = msg.build_message()

    attachment = message["attachments"][0]
    assert message["body"]["content"] == f'<attachment id="{attachment["id"]}"></attachment>'
    card = json.loads(attachment["content"])
    assert card["type"] == "AdaptiveCard"
    header = card["body"][0]
    assert header["type"] == "Container" and header["style"] == "attention"
    assert "KubePodCrashLooping" in header["items"][1]["text"]
    assert card["body"][1] == {"type": "ActionSet", "actions": [{"type": "Action.OpenUrl", "title": "Investigate 🔎", "url": ANY}]}
    text = json.dumps(card)
    assert "Crash info" in text and "OOMKilled" in text and "line 2" in text
    assert message["hostedContents"][0]["contentType"] == "image/png"
    assert "../hostedContents/1/$value" in text

    without_images = MsTeamsGraphMsg.without_images(message)
    assert "hostedContents" not in without_images
    assert "hostedContents" not in without_images["attachments"][0]["content"]


def test_sender_retries_without_images_when_rejected():
    client = MagicMock()
    client.post_channel_message.side_effect = [ok_response(400, {"error": {"message": "bad image"}}), ok_response()]
    client.error_message.return_value = "bad image"
    sender = MsTeamsGraphSender(client, "account", "test-cluster", False, send_files=True)

    sender.send_finding(finding_with_blocks(), False, TEAM, DEFAULT_CHANNEL)

    assert client.post_channel_message.call_count == 2
    assert "hostedContents" not in client.post_channel_message.call_args_list[1].args[2]
