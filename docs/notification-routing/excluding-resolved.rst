Exclude "Resolved" Notifications
===================================

Configure Robusta to not send notifications for issues that are resolved. This helps you reduce noise and focus on just firing alerts 

.. code-block:: yaml

    sinksConfig:
    - slack_sink:
        name: high_severity_sink
        slack_channel: high-severity-notifications
        api_key: secret-key
        scope:
        exclude:
            - title: ".*RESOLVED.*"