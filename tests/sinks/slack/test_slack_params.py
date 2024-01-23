import logging

from robusta.core.sinks.slack import SlackSinkParams


def test_channel_override():
    # channel_override supported formats (from the docs: https://docs.robusta.dev/master/configuration/sinks/slack.html#dynamic-slack-channels)
    # channel_override: "labels.slack"
    # channel_override: "$labels.slack"
    # channel_override: "${annotations.kubernetes.io/service-name}"
    # channel_override: "$cluster_name-alerts-$labels.env-${annotations.kubernetes.io/service-name}"
    # channel_override: cluster_name
    # channel_override: $cluster_name
    # channel_override: annotations.slack
    # channel_override: $annotations.slack

    # tests
    OVERRIDE_CHANNEL = "override-channel"
    DEFAULT_CHANNEL = "default-channel"

    # channel_override: cluster_name
    test_channel_override_config = "cluster_name"
    params = SlackSinkParams(
        name="test sink",
        slack_channel=DEFAULT_CHANNEL,
        api_key="xiob-test",
        channel_override=test_channel_override_config,
    )
    logging.info(f"testing {test_channel_override_config}")

    labels = {"slack": OVERRIDE_CHANNEL}
    annotations = {}
    channel = params.get_slack_channel("test cluster", labels, annotations)
    assert channel == "test cluster", f"{test_channel_override_config} override channel not found"

    # channel_override: $cluster_name
    test_channel_override_config = "$cluster_name"
    params = SlackSinkParams(
        name="test sink",
        slack_channel=DEFAULT_CHANNEL,
        api_key="xiob-test",
        channel_override=test_channel_override_config,
    )
    logging.info(f"testing {test_channel_override_config}")

    labels = {"slack": OVERRIDE_CHANNEL}
    annotations = {}
    channel = params.get_slack_channel("test cluster", labels, annotations)
    assert channel == "test cluster", f"{test_channel_override_config} override channel not found"

    # channel_override: "labels.slack"
    test_channel_override_config = "labels.slack"
    params = SlackSinkParams(
        name="test sink",
        slack_channel=DEFAULT_CHANNEL,
        api_key="xiob-test",
        channel_override=test_channel_override_config,
    )
    logging.info(f"testing {test_channel_override_config}")

    labels = {"slack": OVERRIDE_CHANNEL}
    annotations = {}
    channel = params.get_slack_channel("test cluster", labels, annotations)
    assert channel == OVERRIDE_CHANNEL, f"{test_channel_override_config} override channel not found"

    labels = {"slac": OVERRIDE_CHANNEL}
    annotations = {}
    channel = params.get_slack_channel("test cluster", labels, annotations)
    assert channel == DEFAULT_CHANNEL, f"{test_channel_override_config} override - default channel not chosen"

    labels = {"slac": OVERRIDE_CHANNEL}
    annotations = {"slack": OVERRIDE_CHANNEL}
    channel = params.get_slack_channel("test cluster", labels, annotations)
    assert channel == DEFAULT_CHANNEL, f"{test_channel_override_config} override - default channel not chosen"

    # channel_override: "$labels.slack"
    test_channel_override_config = "$labels.slack"
    params = SlackSinkParams(
        name="test sink",
        slack_channel=DEFAULT_CHANNEL,
        api_key="xiob-test",
        channel_override=test_channel_override_config,
    )
    logging.info(f"testing {test_channel_override_config}")

    labels = {"slack": OVERRIDE_CHANNEL}
    annotations = {}
    channel = params.get_slack_channel("test cluster", labels, annotations)
    assert channel == OVERRIDE_CHANNEL, f"{test_channel_override_config} override channel not found"

    labels = {"slac": OVERRIDE_CHANNEL}
    annotations = {}
    channel = params.get_slack_channel("test cluster", labels, annotations)
    assert channel == DEFAULT_CHANNEL, f"{test_channel_override_config} override - default channel not chosen"

    labels = {"slac": OVERRIDE_CHANNEL}
    annotations = {"slack": OVERRIDE_CHANNEL}
    channel = params.get_slack_channel("test cluster", labels, annotations)
    assert channel == DEFAULT_CHANNEL, f"{test_channel_override_config} override - default channel not chosen"

    # channel_override: annotations.slack
    test_channel_override_config = "annotations.slack"
    params = SlackSinkParams(
        name="test sink",
        slack_channel=DEFAULT_CHANNEL,
        api_key="xiob-test",
        channel_override=test_channel_override_config,
    )
    logging.info(f"testing {test_channel_override_config}")

    labels = {}
    annotations = {"slack": OVERRIDE_CHANNEL}
    channel = params.get_slack_channel("test cluster", labels, annotations)
    assert channel == OVERRIDE_CHANNEL, f"{test_channel_override_config} override channel not found"

    labels = {}
    annotations = {"slac": OVERRIDE_CHANNEL}
    channel = params.get_slack_channel("test cluster", labels, annotations)
    assert channel == DEFAULT_CHANNEL, f"{test_channel_override_config} override - default channel not chosen"

    labels = {"slack": OVERRIDE_CHANNEL}
    annotations = {"slac": OVERRIDE_CHANNEL}
    channel = params.get_slack_channel("test cluster", labels, annotations)
    assert channel == DEFAULT_CHANNEL, f"{test_channel_override_config} override - default channel not chosen"

    # channel_override: $annotations.slack
    test_channel_override_config = "$annotations.slack"
    params = SlackSinkParams(
        name="test sink",
        slack_channel=DEFAULT_CHANNEL,
        api_key="xiob-test",
        channel_override=test_channel_override_config,
    )
    logging.info(f"testing {test_channel_override_config}")

    labels = {}
    annotations = {"slack": OVERRIDE_CHANNEL}
    channel = params.get_slack_channel("test cluster", labels, annotations)
    assert channel == OVERRIDE_CHANNEL, f"{test_channel_override_config} override channel not found"

    labels = {}
    annotations = {"slac": OVERRIDE_CHANNEL}
    channel = params.get_slack_channel("test cluster", labels, annotations)
    assert channel == DEFAULT_CHANNEL, f"{test_channel_override_config} override - default channel not chosen"

    labels = {"slack": OVERRIDE_CHANNEL}
    annotations = {"slac": OVERRIDE_CHANNEL}
    channel = params.get_slack_channel("test cluster", labels, annotations)
    assert channel == DEFAULT_CHANNEL, f"{test_channel_override_config} override - default channel not chosen"

    # channel_override: "${annotations.kubernetes.io/service-name}"
    test_channel_override_config = "${annotations.kubernetes.io/service-name}"
    logging.info(f"testing {test_channel_override_config}")
    params = SlackSinkParams(
        name="test sink",
        slack_channel=DEFAULT_CHANNEL,
        api_key="xiob-test",
        channel_override=test_channel_override_config,
    )

    labels = {}
    annotations = {"kubernetes.io/service-name": OVERRIDE_CHANNEL}
    channel = params.get_slack_channel("test cluster", labels, annotations)
    assert channel == OVERRIDE_CHANNEL, f"{test_channel_override_config} override channel not found"

    labels = {}
    annotations = {"kubernetes.io/service": OVERRIDE_CHANNEL}
    channel = params.get_slack_channel("test cluster", labels, annotations)
    assert channel == DEFAULT_CHANNEL, f"{test_channel_override_config} override - default channel not chosen"

    labels = {"kubernetes.io/service": OVERRIDE_CHANNEL}
    annotations = {}
    channel = params.get_slack_channel("test cluster", labels, annotations)
    assert channel == DEFAULT_CHANNEL, f"{test_channel_override_config} override - default channel not chosen"

    # channel_override: "$cluster_name-alerts-$labels.env-${annotations.kubernetes.io/service-name}"
    test_channel_override_config = "$cluster_name-alerts-$labels.env-${annotations.kubernetes.io/service-name}"
    logging.info(f"testing {test_channel_override_config}")

    params = SlackSinkParams(
        name="test sink",
        slack_channel=DEFAULT_CHANNEL,
        api_key="xiob-test",
        channel_override=test_channel_override_config,
    )

    labels = {"env": "xxx"}
    annotations = {"kubernetes.io/service-name": "yyy"}
    channel = params.get_slack_channel("test cluster", labels, annotations)
    assert channel == "test cluster-alerts-xxx-yyy", f"{test_channel_override_config} override channel not found"

    labels = {"env123": "xxx"}
    annotations = {"kubernetes.io/service-name": "yyy"}
    channel = params.get_slack_channel("test cluster", labels, annotations)
    assert channel == DEFAULT_CHANNEL, f"{test_channel_override_config} override - default channel not chosen"

    labels = {"kubernetes.io/service": OVERRIDE_CHANNEL}
    annotations = {"env": "xxx"}
    channel = params.get_slack_channel("test cluster", labels, annotations)
    assert channel == DEFAULT_CHANNEL, f"{test_channel_override_config} override - default channel not chosen"

    test_channel_override_config = "$cluster_name-alerts-$labels.env-$annotations.zone-channel"
    logging.info(f"testing {test_channel_override_config}")

    params = SlackSinkParams(
        name="test sink",
        slack_channel=DEFAULT_CHANNEL,
        api_key="xiob-test",
        channel_override=test_channel_override_config,
    )

    labels = {"env": "xxx"}
    annotations = {"zone": "yyy"}
    channel = params.get_slack_channel("test cluster", labels, annotations)
    assert (
        channel == "test cluster-alerts-xxx-yyy-channel"
    ), f"{test_channel_override_config} override channel not found"
