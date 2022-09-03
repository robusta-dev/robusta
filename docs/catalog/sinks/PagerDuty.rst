PagerDuty
##########

Robusta can send playbooks results to the PagerDuty alerts API.

| To configure PagerDuty, a PagerDuty Integration API Key (string) and a PagerDuty Integration URL (url) is needed.

Configuring the PagerDuty sink
------------------------------------------------

.. admonition:: values.yaml

    .. code-block:: yaml

        sinks_config:
            - pagerduty_sink:
                name: main_pagerduty_sink
                api_key: <api key> # e.g. f653634653463678fadas43534506
                url: <url> # e.g.  https://events.pagerduty.com/v2/enqueue/
