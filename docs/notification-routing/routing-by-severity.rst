Route by Severity
==============================

To configure Slack so that only high-severity alerts go to one channel and everything else goes to another, use the following configuration example:

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