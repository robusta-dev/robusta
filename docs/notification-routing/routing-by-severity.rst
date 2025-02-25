Route by Severity
==============================

Configure Slack to send high-severity alerts to one channel and all others to another using this example:

.. code-block:: yaml

    sinksConfig:
    - slack_sink:
        name: high_severity_sink
        slack_channel: high-severity-notifications
        api_key: secret-key
        scope:
        include:
            - severity: HIGH
              source: PROMETHEUS # optional: send only alerts originating from Prometheus (not Robusta's APIServer detections like OOMKills and CrashLoops)

    - slack_sink:
        name: other_severity_sink
        slack_channel: other-notifications
        api_key: secret-key
        scope:
        exclude: # excludes so you don't get the same alert in two channels
            - severity: HIGH
              source: PROMETHEUS


**Important:** ``severity`` above refers to the Robusta severity for this alert. :ref:`Robusta maps Prometheus severities onto standardized levels.<Mapping Custom Alert Severity>`. When specifying the severity, use the Robusta severity not the original Prometheus severity.

