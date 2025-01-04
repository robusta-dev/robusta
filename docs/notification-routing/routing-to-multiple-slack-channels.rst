Multiple Slack Channels 
####################################

In this example, we'll route alerts to different Slack channels depending on an alert's attributes:

.. code-block:: yaml

    sinksConfig:
    - slack_sink:
        name: frontend_sink
        slack_channel: frontend-notifications
        api_key: secret-key
        scope:
            include:
            - namespace: [frontend]

    - slack_sink:
        name: backend_sink
        slack_channel: backend-notifications
        api_key: secret-key
        scope:
            include:
            - namespace: [backend]

