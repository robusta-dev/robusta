import logging

import pytest

from robusta.core.sinks.msteams.msteams_webhook_tranformer import MsTeamsWebhookUrlTransformer

OVERRIDE_WEBHOOK = "override-webhook-url"
DEFAULT_WEBHOOK = "default-webhook-url"


testdata_template = [
    (
        "annotations.msteams",
        {"msteams": OVERRIDE_WEBHOOK},
        OVERRIDE_WEBHOOK,
        "override channel not found",
    ),
    (
        "annotations.msteams",
        {"msteam": OVERRIDE_WEBHOOK},
        DEFAULT_WEBHOOK,
        "override - default channel not found",
    ),
    (
        "$annotations.msteams",
        {"msteams": OVERRIDE_WEBHOOK},
        OVERRIDE_WEBHOOK,
        "override - default channel not chosen",
    ),
    (
        "$annotations.msteams",
        {"variable": OVERRIDE_WEBHOOK},
        DEFAULT_WEBHOOK,
        "override - default channel not chosen",
    ),
    (
        "${annotations.kubernetes.io/service-name}",
        {"kubernetes.io/service-name": OVERRIDE_WEBHOOK},
        OVERRIDE_WEBHOOK,
        "override channel not found",
    ),
    (
        "${annotations.kubernetes.io/service-name}",
        {"kubernetes.io/service": OVERRIDE_WEBHOOK},
        DEFAULT_WEBHOOK,
        "override - default channel not chosen",
    ),
    (
        "${annotations.kubernetes.io/service-name}",
        {},
        DEFAULT_WEBHOOK,
        "override - default channel not chosen",
    ),
    # webhook_override: "$cluster_name-alerts-$annotations.env-${annotations.kubernetes.io/service-name}"
    (
        "$cluster_name-alerts-$annotations.env-${annotations.kubernetes.io/service-name}",
        {"kubernetes.io/service-name": "yyy"},
        DEFAULT_WEBHOOK,
        "override channel not found",
    ),
    (
        "$cluster_name-alerts-$annotations.env-${annotations.kubernetes.io/service-name}",
        {"kubernetes.io/service-name": "yyy"},
        DEFAULT_WEBHOOK,
        "override - default channel not chosen",
    ),
]


@pytest.mark.parametrize("webhook_override, annotations, expected, error", testdata_template)
def test_ms_teams_template(webhook_override, annotations, expected, error):
    logging.info(f"testing {webhook_override}")
    webhook_url = MsTeamsWebhookUrlTransformer.template(
        webhook_override=webhook_override,
        default_webhook_url=DEFAULT_WEBHOOK,
        annotations=annotations,
    )
    assert webhook_url == expected, f"{webhook_override} {error}"


testdata_validate = [
    ("annotations.team", "$annotations.team", "missing '$' prefix"),
    ("$annotations.team", "$annotations.team", "override should be left unchanged"),
    ("${annotations.team}", "${annotations.team}", "override should be left unchanged"),
]


@pytest.mark.parametrize("webhook_override, expected, error", testdata_validate)
def test_ms_teams_validate_webhook_override(webhook_override, expected, error):
    logging.info(f"testing {webhook_override}")
    webhook_url = MsTeamsWebhookUrlTransformer.validate_webhook_override(webhook_override)
    assert webhook_url == expected, f"{webhook_override} {error}"


testdata_should_throw = [
    "cluste_name",
    "annotations.",
    "$annotations.",
    "invalid.something",
    "labels.",
    "$labels.",
    "test",
]


@pytest.mark.parametrize("webhook_override", testdata_should_throw)
def test_ms_teams_validate_webhook_override_should_throw(webhook_override):
    logging.info(f"testing {webhook_override}")
    with pytest.raises(ValueError):
        MsTeamsWebhookUrlTransformer.validate_webhook_override(webhook_override)
