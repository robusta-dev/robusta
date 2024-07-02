from unittest.mock import patch

import pytest

from robusta.core.sinks.msteams.msteams_webhook_tranformer import MsTeamsWebhookUrlTransformer

DEFAULT_WEBHOOK_URL = "http://example-default-webhook.com"
OVERRIDE_WEBHOOK_URL = "http://example.com"
OVERRIDE_CONTAINING_ENV_NAME = "WEBHOOK_VALUE"
ENV_MOCK_WITH_EMPTY_WEBHOOK_VALUE = None
ENV_MOCK_WITH_WEBHOOK_URL = "http://from-env-example.com"
VALID_URLS_LIST = [
    "http://example.com",
    "https://example.com",
    "http://127.0.0.1",
    "http://127.0.0.1:8080",
    "http://example.com/path?query=string",
    "https://example.com:443/path/to/resource?query=param#fragment",
]
INVALID_URLS_LIST = [
    "example.com",
    "ftp://example.com",
    "http://example",
    "http://example.com/path with spaces",
    "http://-example.com",
]


@pytest.mark.parametrize(
    "webhook_override, annotations, expected, error, env_value",
    [
        (
            "annotations.msteams",
            {"msteams": OVERRIDE_WEBHOOK_URL},
            OVERRIDE_WEBHOOK_URL,
            "override channel not found",
            ENV_MOCK_WITH_EMPTY_WEBHOOK_VALUE,
        ),
        (
            "annotations.msteams",
            {"msteams": OVERRIDE_CONTAINING_ENV_NAME},
            ENV_MOCK_WITH_WEBHOOK_URL,
            "env with webhook value is not found",
            ENV_MOCK_WITH_WEBHOOK_URL,
        ),
        (
            "annotations.msteams",
            {"msteam": OVERRIDE_WEBHOOK_URL},
            DEFAULT_WEBHOOK_URL,
            "override - default channel not found",
            ENV_MOCK_WITH_EMPTY_WEBHOOK_VALUE,
        ),
        (
            "$annotations.msteams",
            {"msteams": OVERRIDE_WEBHOOK_URL},
            OVERRIDE_WEBHOOK_URL,
            "override - default channel not chosen",
            ENV_MOCK_WITH_EMPTY_WEBHOOK_VALUE,
        ),
        (
            "$annotations.msteams",
            {"variable": OVERRIDE_WEBHOOK_URL},
            DEFAULT_WEBHOOK_URL,
            "override - default channel not chosen",
            ENV_MOCK_WITH_EMPTY_WEBHOOK_VALUE,
        ),
        (
            "${annotations.kubernetes.io/service-name}",
            {"kubernetes.io/service-name": OVERRIDE_WEBHOOK_URL},
            OVERRIDE_WEBHOOK_URL,
            "override channel not found",
            ENV_MOCK_WITH_EMPTY_WEBHOOK_VALUE,
        ),
        (
            "${annotations.kubernetes.io/service-name}",
            {"kubernetes.io/service": OVERRIDE_WEBHOOK_URL},
            DEFAULT_WEBHOOK_URL,
            "override - default channel not chosen",
            ENV_MOCK_WITH_EMPTY_WEBHOOK_VALUE,
        ),
        (
            "${annotations.kubernetes.io/service-name}",
            {},
            DEFAULT_WEBHOOK_URL,
            "override - default channel not chosen",
            ENV_MOCK_WITH_EMPTY_WEBHOOK_VALUE,
        ),
        (
            "$cluster_name-alerts-$annotations.env-${annotations.kubernetes.io/service-name}",
            {"kubernetes.io/service-name": "yyy"},
            DEFAULT_WEBHOOK_URL,
            "override channel not found",
            ENV_MOCK_WITH_EMPTY_WEBHOOK_VALUE,
        ),
        (
            "$cluster_name-alerts-$annotations.env-${annotations.kubernetes.io/service-name}",
            {"kubernetes.io/service-name": "yyy"},
            DEFAULT_WEBHOOK_URL,
            "override - default channel not chosen",
            ENV_MOCK_WITH_EMPTY_WEBHOOK_VALUE,
        ),
    ],
)
def test_ms_teams_webhook_transformer_template_method(webhook_override, annotations, expected, error, env_value):
    with patch("robusta.core.sinks.msteams.msteams_webhook_tranformer.os.getenv", return_value=env_value):
        webhook_url = MsTeamsWebhookUrlTransformer.template(
            webhook_override=webhook_override,
            default_webhook_url=DEFAULT_WEBHOOK_URL,
            annotations=annotations,
        )
        assert webhook_url == expected, f"{webhook_override} {error}"


@pytest.mark.parametrize(
    "webhook_override, env_value, expected, error",
    [
        (VALID_URLS_LIST[0], ENV_MOCK_WITH_EMPTY_WEBHOOK_VALUE, VALID_URLS_LIST[0], "webhook url is not valid"),
        (VALID_URLS_LIST[1], ENV_MOCK_WITH_EMPTY_WEBHOOK_VALUE, VALID_URLS_LIST[1], "webhook url is not valid"),
        (VALID_URLS_LIST[2], ENV_MOCK_WITH_EMPTY_WEBHOOK_VALUE, VALID_URLS_LIST[2], "webhook url is not valid"),
        (VALID_URLS_LIST[3], ENV_MOCK_WITH_EMPTY_WEBHOOK_VALUE, VALID_URLS_LIST[3], "webhook url is not valid"),
        (VALID_URLS_LIST[4], ENV_MOCK_WITH_EMPTY_WEBHOOK_VALUE, VALID_URLS_LIST[4], "webhook url is not valid"),
        (VALID_URLS_LIST[5], ENV_MOCK_WITH_EMPTY_WEBHOOK_VALUE, VALID_URLS_LIST[5], "webhook url is not valid"),
        (INVALID_URLS_LIST[0], ENV_MOCK_WITH_WEBHOOK_URL, ENV_MOCK_WITH_WEBHOOK_URL, "webhook url is not valid"),
        (INVALID_URLS_LIST[1], ENV_MOCK_WITH_WEBHOOK_URL, ENV_MOCK_WITH_WEBHOOK_URL, "webhook url is not valid"),
        (INVALID_URLS_LIST[2], ENV_MOCK_WITH_WEBHOOK_URL, ENV_MOCK_WITH_WEBHOOK_URL, "webhook url is not valid"),
        (INVALID_URLS_LIST[3], ENV_MOCK_WITH_WEBHOOK_URL, ENV_MOCK_WITH_WEBHOOK_URL, "webhook url is not valid"),
        (INVALID_URLS_LIST[4], ENV_MOCK_WITH_WEBHOOK_URL, ENV_MOCK_WITH_WEBHOOK_URL, "webhook url is not valid"),
    ],
)
def test_ms_teams_webhook_transformer_validate_url_or_get_env_method(webhook_override, expected, env_value, error):
    with patch("robusta.core.sinks.msteams.msteams_webhook_tranformer.os.getenv", return_value=env_value):
        webhook_url = MsTeamsWebhookUrlTransformer.validate_url_or_get_env(
            webhook_url=webhook_override, default_webhook_url=DEFAULT_WEBHOOK_URL
        )
        assert webhook_url == expected, f"{webhook_override} {error}"


@pytest.mark.parametrize(
    "webhook_override, expected, error",
    [
        ("annotations.team", "$annotations.team", "missing '$' prefix"),
        ("$annotations.team", "$annotations.team", "override should be left unchanged"),
        ("${annotations.team}", "${annotations.team}", "override should be left unchanged"),
    ],
)
def test_ms_teams_webhook_transformer_validate_webhook_override_method(webhook_override, expected, error):
    webhook_url = MsTeamsWebhookUrlTransformer.validate_webhook_override(webhook_override)
    assert webhook_url == expected, f"{webhook_override} {error}"


@pytest.mark.parametrize(
    "webhook_override",
    [
        "cluste_name",
        "annotations.",
        "$annotations.",
        "invalid.something",
        "labels.",
        "$labels.",
        "test",
    ],
)
def test_ms_teams_webhook_transformer_validate_webhook_override_raises_error(webhook_override):
    with pytest.raises(ValueError):
        MsTeamsWebhookUrlTransformer.validate_webhook_override(webhook_override)
