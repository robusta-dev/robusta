import logging

import pytest

from robusta.core.sinks.common import ChannelTransformer

# channel_override supported formats (from the docs: https://docs.robusta.dev/master/configuration/sinks/slack.html#dynamic-slack-channels)
# channel_override: "labels.slack"
# channel_override: "$labels.slack"
# channel_override: "${annotations.kubernetes.io/service-name}"
# channel_override: "$cluster_name-alerts-$labels.env-${annotations.kubernetes.io/service-name}"
# channel_override: cluster_name
# channel_override: $cluster_name
# channel_override: annotations.slack
# channel_override: $annotations.slack

OVERRIDE_CHANNEL = "override-channel"
DEFAULT_CHANNEL = "default-channel"
CLUSTER_NAME = "test cluster"

testdata = [
    # channel_override: cluster_name
    (
        "cluster_name",
        {"slack": OVERRIDE_CHANNEL},
        {},
        CLUSTER_NAME,
        "override channel not found",
    ),
    # channel_override: $cluster_name
    (
        "$cluster_name",
        {"slack": OVERRIDE_CHANNEL},
        {},
        CLUSTER_NAME,
        "override channel not found",
    ),
    # channel_override: "labels.slack"
    (
        "labels.slack",
        {"slack": OVERRIDE_CHANNEL},
        {},
        OVERRIDE_CHANNEL,
        "override channel not found",
    ),
    (
        "labels.slack",
        {"slac": OVERRIDE_CHANNEL},
        {},
        DEFAULT_CHANNEL,
        "override - default channel not chosen",
    ),
    (
        "labels.slack",
        {"slac": OVERRIDE_CHANNEL},
        {"slack": OVERRIDE_CHANNEL},
        DEFAULT_CHANNEL,
        "override - default channel not chosen",
    ),
    (
        "$labels.slack",
        {"slac": OVERRIDE_CHANNEL},
        {},
        DEFAULT_CHANNEL,
        "override - default channel not chosen",
    ),
    (
        "$labels.slack",
        {"slac": OVERRIDE_CHANNEL},
        {"slack": OVERRIDE_CHANNEL},
        DEFAULT_CHANNEL,
        "override - default channel not chosen",
    ),
    # channel_override: annotations.slack
    (
        "annotations.slack",
        {},
        {"slack": OVERRIDE_CHANNEL},
        OVERRIDE_CHANNEL,
        "override channel not found",
    ),
    (
        "annotations.slack",
        {},
        {"slac": OVERRIDE_CHANNEL},
        DEFAULT_CHANNEL,
        "override - default channel not found",
    ),
    (
        "annotations.slack",
        {"slack": OVERRIDE_CHANNEL},
        {"slac": OVERRIDE_CHANNEL},
        DEFAULT_CHANNEL,
        "override - default channel not chosen",
    ),
    # channel_override: $annotations.slack
    (
        "$annotations.slack",
        {},
        {"slack": OVERRIDE_CHANNEL},
        OVERRIDE_CHANNEL,
        "override channel not found",
    ),
    (
        "$annotations.slack",
        {},
        {"slac": OVERRIDE_CHANNEL},
        DEFAULT_CHANNEL,
        "override - default channel not chosen",
    ),
    (
        "$annotations.slack",
        {"slack": OVERRIDE_CHANNEL},
        {"slac": OVERRIDE_CHANNEL},
        DEFAULT_CHANNEL,
        "override - default channel not chosen",
    ),
    # channel_override: "${annotations.kubernetes.io/service-name}"
    (
        "${annotations.kubernetes.io/service-name}",
        {},
        {"kubernetes.io/service-name": OVERRIDE_CHANNEL},
        OVERRIDE_CHANNEL,
        "override channel not found",
    ),
    (
        "${annotations.kubernetes.io/service-name}",
        {},
        {"kubernetes.io/service": OVERRIDE_CHANNEL},
        DEFAULT_CHANNEL,
        "override - default channel not chosen",
    ),
    (
        "${annotations.kubernetes.io/service-name}",
        {"kubernetes.io/service": OVERRIDE_CHANNEL},
        {},
        DEFAULT_CHANNEL,
        "override - default channel not chosen",
    ),
    # channel_override: "$cluster_name-alerts-$labels.env-${annotations.kubernetes.io/service-name}"
    (
        "$cluster_name-alerts-$labels.env-${annotations.kubernetes.io/service-name}",
        {"env": "xxx"},
        {"kubernetes.io/service-name": "yyy"},
        "test cluster-alerts-xxx-yyy",
        "override channel not found",
    ),
    (
        "$cluster_name-alerts-$labels.env-${annotations.kubernetes.io/service-name}",
        {"env123": "xxx"},
        {"kubernetes.io/servie-name": "yyy"},
        DEFAULT_CHANNEL,
        "override - default channel not chosen",
    ),
    (
        "$cluster_name-alerts-$labels.env-${annotations.kubernetes.io/service-name}",
        {"kubernetes.io/service": OVERRIDE_CHANNEL},
        {"env": "xxx"},
        DEFAULT_CHANNEL,
        "override - default channel not chosen",
    ),
    (
        "$cluster_name-alerts-$labels.env-$annotations.zone-channel",
        {"env": "xxx"},
        {"zone": "yyy"},
        "test cluster-alerts-xxx-yyy-channel",
        "override channel not found",
    ),
]


@pytest.mark.parametrize("channel_override_config, labels, annotations, expected, error", testdata)
def test_channel_transformer(channel_override_config, labels, annotations, expected, error):
    logging.info(f"testing {channel_override_config}")
    channel = ChannelTransformer.template(
        channel_override=channel_override_config,
        default_channel=DEFAULT_CHANNEL,
        cluster_name=CLUSTER_NAME,
        labels=labels,
        annotations=annotations,
    )
    assert channel == expected, f"{channel_override_config} {error}"
