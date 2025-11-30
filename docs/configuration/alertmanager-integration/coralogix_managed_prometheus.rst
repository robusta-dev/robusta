Coralogix Alerts
*****************

This guide shows how to send alerts from Coralogix to Robusta.

For configuring metric querying from Coralogix Prometheus, see :doc:`/configuration/metric-providers-coralogix`.

Send Alerts to Robusta
===============================

This integration lets you send Coralogix alerts to Robusta.

You need to create two webhooks: one for firing alerts and one for resolved alerts.

Common Configuration (for both webhooks)
-----------------------------------------

1. In the Coralogix site go to Data Flow, then Outbound Webhooks, and click ``Generic webhook``.
2. In the url insert:

.. code-block::

    https://api.robusta.dev/integrations/generic/alertmanager

3. Select the Post Method.
4. In the Edit headers replace it with

.. code-block:: json

    {
      "Content-Type": "application/json",
      "Authorization": "Bearer <TOKEN>" # where token is '<ACCOUNT_ID> <SIGNING_KEY>'
    }


Firing Alerts Webhook
---------------------

5. Configure this webhook to trigger on **firing** alerts (when alerts are triggered/started).
6. For the firing alerts webhook, in Edit body add:

.. code-block:: json

    {
      "externalURL": "",
      "groupKey": "coralogix/alert:${ALERT_ID}",
      "version": "1",
      "status": "firing",
      "receiver": "robusta receiver",
      "alerts": [
        {
          "status": "firing",
          "startsAt": "$EVENT_TIMESTAMP_ISO",
          "endsAt": "1970-01-01T00:00:00Z",
          "generatorURL": "$ALERT_URL",
          "source": "Coralogix",
          "description": "$ALERT_DESCRIPTION",
          "fingerprint": "$ALERT_UNIQUE_IDENTIFIER",
          "annotations": {},
          "labels": {
            "cluster_name": "MY_CLUSTER_NAME", # make sure to add your cluster name here for this webhook. Both "cluster" or "cluster_name" labels are also supported
            "alertname": "$ALERT_NAME",
            "severity": "$EVENT_SEVERITY",
            "application": "$APPLICATION_NAME",
            "subsystem": "$SUBSYSTEM_NAME",
            "team": "$TEAM_NAME",
            "alert_url": "$ALERT_URL"
            # Add any additional alert specific fields here
            # see here for more parameters https://coralogix.com/docs/alert-webhooks/#custom-alert-webhooks
          }
        }
      ]
    }

7. Click the 'Test Config' button and check your robusta sink for a "Test configuration" alert.
8. Click Save

Resolved Alerts Webhook
-----------------------

9. Create a second webhook following steps 1-4 above with the same URL and headers.
10. Configure this webhook to trigger on **resolved** alerts (when alerts are resolved/ended).
11. For the resolved alerts webhook, in Edit body add:

.. code-block:: json

    {
      "externalURL": "",
      "groupKey": "coralogix/alert:${ALERT_ID}",
      "version": "1",
      "status": "resolved",
      "receiver": "robusta receiver",
      "alerts": [
        {
          "status": "resolved",
          "startsAt": "$EVENT_TIMESTAMP_ISO",
          "endsAt": "$EVENT_TIMESTAMP_ISO",
          "generatorURL": "$ALERT_URL",
          "source": "Coralogix",
          "description": "$ALERT_DESCRIPTION",
          "fingerprint": "$ALERT_UNIQUE_IDENTIFIER",
          "annotations": {},
          "labels": {
            "cluster_name": "MY_CLUSTER_NAME", # make sure to add your cluster name here for this webhook. Both "cluster" or "cluster_name" labels are also supported
            "alertname": "$ALERT_NAME",
            "severity": "$EVENT_SEVERITY",
            "application": "$APPLICATION_NAME",
            "subsystem": "$SUBSYSTEM_NAME",
            "team": "$TEAM_NAME",
            "alert_url": "$ALERT_URL"
          }
        }
      ]
    }

12. Click the 'Test Config' button and check your robusta sink for a "Test configuration" alert.
13. Click Save

.. note::
   Make sure to update the ``cluster_name`` value in both webhook bodies to match your cluster name. Both "cluster" or "cluster_name" labels are also supported.
   For more parameters, see `Coralogix alert webhooks documentation <https://coralogix.com/docs/alert-webhooks/#custom-alert-webhooks>`_.


Configure Metric Querying
==============================

To enable Robusta to pull metrics from Coralogix Prometheus, see :doc:`/configuration/metric-providers-coralogix` metrics provider settings.
