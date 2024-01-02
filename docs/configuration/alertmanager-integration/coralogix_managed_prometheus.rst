Coralogix Managed Prometheus
********************************

This guide walks you through integrating your Coralogix managed Prometheus with Robusta. You will need to configure two integrations: one to send alerts to Robusta and another to let Robusta query metrics and create silences.

Configure Metric Querying
==============================

Metrics querying lets Robusta pull metrics from Coralogix Managed Prometheus.

1. Go to `Coralogix Documentation <https://coralogix.com/docs/grafana-plugin/#block-1778265e-61c2-4362-9060-533d158857d7>`_ and choose the relevant 'PromQL Endpoint' from their table.
2. In your `generated_values.yaml` file add the endpoint url:

.. code-block:: yaml

  # this line should already exist
  globalConfig:
      prometheus_url: "<YOUR_PROM_API_LINK_HERE>" #for example https://prom-api.coralogix.com
      # To add any labels that are relevant to the specific cluster uncomment and change the lines below (optional)
      # prometheus_additional_labels:
      #   cluster: 'CLUSTER_NAME_HERE'

      # Create alert silencing when using Grafana alerts (optional)
      # grafana_api_key: <YOUR GRAFANA EDITOR API KEY> # (1)
      # alertmanager_flavor: grafana

.. code-annotations::
    1. This is necessary for Robusta to create silences when using Grafana Alerts, because of minor API differences in the AlertManager embedded in Grafana.


3. On the Coralogix site, go to Data Flow -> Api Keys and copy the 'Logs Query Key'

.. note:: If one does not exist you will have to generate a new one by clicking 'GENERATE NEW API KEY'

4. Create a secret in your cluster with your key logs_query_key and the value as the key you just copied

5. In your generated_values.yaml file add the following environment variables from the previous step replacing MY_CORLOGIX_SECRET with your secret name.

.. code-block:: yaml

  runner:
    additional_env_vars:
    - name: PROMETHEUS_SSL_ENABLED
      value: "true"
    - name: CORALOGIX_PROMETHEUS_TOKEN
      valueFrom:
        secretKeyRef:
          name: MY_CORALOGIX_SECRET
          key: logs_query_key

Send alerts to Robusta
===============================

This integration lets you send Coralogix alerts to Robusta.

.. note:: Many of the fields supported in Alertmanager dont in Coralogix alerts

To configure it:

1. In the Coralogix site go to Data Flow and in the Webhook section click ``Webhook``.
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

5. In Edit body add

.. code-block:: json

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

6. Click the 'Test Config' button and check your robusta sinks that you received an alert
7. Click Save
