Coralogix Alerts
*****************

This guide shows how to send alerts from Coralogix to Robusta.

For configuring metric querying from Coralogix Prometheus, see :doc:`/configuration/metric-providers-coralogix`.

Send Alerts to Robusta
===============================

This integration lets you send Coralogix alerts to Robusta.

To configure it:

1. In the Coralogix site go to Data Flow, then Outbound Webhooks, and click ``Generic webhook``.
2. In the url insert:

.. code-block::

    https://api.robusta.dev/integrations/generic/alertmanager

3. Select the Post Method.
4. In the Edit headers replace it with

.. code-block:: yaml

    {
      "Content-Type": "application/json",
      "Authorization": "Bearer <TOKEN>" # where token is '<ACCOUNT_ID> <SIGNING_KEY>'
    }

5. In Edit body add

.. code-block:: yaml

    {
      "externalURL": "",
      "groupKey": "{}/{}:{}",
      "version": "1",
      "status": "firing",
      "receiver": "robusta receiver",
      "alerts": [
        {
          "description": "$ALERT_DESCRIPTION",
          "status": "firing",
          "endsAt": "$EVENT_TIMESTAMP_MS",
          "startsAt": "$EVENT_TIMESTAMP_MS",
          "generatorURL": "$ALERT_URL",
          "annotations": {},
          "labels": {
            "cluster_name": "MY_CLUSTER_NAME", # make sure to add your cluster name here for this webhook. Both "cluster" or "cluster_name" labels are also supported
            "alertname": "$ALERT_NAME",
            "alert_url": "$ALERT_URL"
            # Add any additional alert specific fields here
            # see here for more parameters https://coralogix.com/docs/alert-webhooks/#custom-alert-webhooks
          }
        }
      ]
    }


6. Click the 'Test Config' button and check your robusta sink for a "Test configuration" alert. 
7. Click Save


Configure Metric Querying
==============================

To enable Robusta to pull metrics from Coralogix Prometheus, see :doc:`/configuration/metric-providers-coralogix` metrics provider settings.
