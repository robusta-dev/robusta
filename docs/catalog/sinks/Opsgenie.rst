Webhook 
###########

Robusta can send playbooks results to a webhook.

.. admonition:: values.yaml

    .. code-block:: yaml

        sinks_config:
        - webhook_sink:
            name: webhook_sink
            url: "https://my-webhook-service.com/robusta-alerts"

**Webhook:**

.. admonition:: This example is sending Robusta notifications to ntfy.sh, push notification service

    .. image:: /images/deployment-babysitter-webhook.png
      :width: 600
      :align: center
