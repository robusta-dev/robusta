Webhook
###########

Robusta can report issues and events in your Kubernetes cluster to a webhook.

.. admonition:: Add this to your generated_values.yaml

    .. code-block:: yaml

        sinksConfig:
        - webhook_sink:
            name: webhook_sink
            url: "https://my-webhook-service.com/robusta-alerts"

Save the file and run

.. code-block:: bash
   :name: cb-add-webhook-sink

    helm upgrade robusta robusta/robusta --values=generated_values.yaml

.. note::

   To secure your webhook URL using Kubernetes Secrets, see :ref:`Managing Secrets`.

**Example Output:**

.. admonition:: This example is sending Robusta notifications to ntfy.sh, push notification service

    .. image:: /images/deployment-babysitter-webhook.png
      :width: 600
      :align: center
