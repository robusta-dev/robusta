Google Managed Alertmanager
===========================

This guide shows how to forward alerts from Google Managed Prometheus (GMP) managed Alertmanager to Robusta using Robusta's generic Alertmanager webhook.

.. note::

   Every alert must carry a ``cluster_name`` label. Set it to the Robusta ``cluster_name`` configured for the target cluster, or use ``external`` when the alerts do not belong to a specific runner.

   For configuring metric querying from Google Managed Prometheus, see :doc:`/configuration/metric-providers-google`. For other Alertmanager integrations, see :doc:`outofcluster-prometheus` or :doc:`alert-manager`.

Requirements
************

- Robusta ``account_id`` and ``signing_key`` from your ``generated_values.yaml`` file.
- A GMP workspace with managed Alertmanager enabled.

Configure the Alertmanager webhook
**********************************

Apply the following Secret in the GMP namespace (default ``gmp-public``). Replace ``<ACCOUNT_ID>`` and ``<SIGNING_KEY>`` with your credentials.

.. code-block:: yaml

   apiVersion: v1
   kind: Secret
   metadata:
     name: alertmanager
     namespace: gmp-public
   type: Opaque
   stringData:
     alertmanager.yaml: |
       receivers:
         - name: 'robusta'
           webhook_configs:
             - url: 'https://api.robusta.dev/integrations/generic/alertmanager'
               http_config:
                 authorization:
                   # Replace <ACCOUNT_ID> <SIGNING_KEY>, with your account_id and signing_key
                   credentials: 'Bearer <ACCOUNT_ID> <SIGNING_KEY>'
               send_resolved: true

       route:
         receiver: 'robusta'
         group_by: ['...']
         group_wait: 1s
         group_interval: 1s
         repeat_interval: 4h

Ensure alerts include ``cluster_name``
*************************************

Use an ``OperatorConfig`` to add external labels to both collection and rule evaluation so every alert contains the required ``cluster_name`` label.

.. code-block:: yaml

   apiVersion: monitoring.googleapis.com/v1
   kind: OperatorConfig
   metadata:
     name: config
     namespace: gmp-public
   collection:
     externalLabels:
       cluster_name: gmp-demo-cluster   # Match your Robusta cluster_name, or use "external"
       location: us-central1-c
       project_id: my-gcp-project
   rules:
     externalLabels:
       cluster_name: gmp-demo-cluster
       location: us-central1-c
       project_id: my-gcp-project

Deploy a demo alert
*******************

Create a simple alerting rule to confirm delivery to Robusta.

.. code-block:: yaml

   apiVersion: monitoring.googleapis.com/v1
   kind: Rules
   metadata:
     name: test-alert
     namespace: gmp-public
   spec:
     groups:
       - name: test
         interval: 30s
         rules:
           - alert: TestAlertForGCPAlertmanager
             expr: vector(1)
             for: 0m
             labels:
               severity: warning
             annotations:
               summary: "Test alert to verify Alertmanager webhook"
               description: "This is a test alert. Delete the Rules resource to stop it."

Optional: verify credentials with curl
**************************************

You can manually validate the webhook and credentials by posting a sample alert:

.. code-block:: bash

   curl -X POST 'https://api.robusta.dev/integrations/generic/alertmanager' \
     -H 'Authorization: Bearer <ACCOUNT_ID> <SIGNING_KEY>' \
     -H 'Content-Type: application/json' \
     -d '{
     "externalURL": "https://console.cloud.google.com/monitoring",
     "groupKey": "gmp/test-alert:gmp-webhook-test-001",
     "version": "1",
     "status": "firing",
     "receiver": "robusta",
     "alerts": [
       {
         "status": "firing",
         "startsAt": "2026-01-13T13:30:50Z",
         "endsAt": "1970-01-01T00:00:00Z",
         "generatorURL": "https://console.cloud.google.com/monitoring",
         "source": "GMP",
         "description": "Test alert to verify GMP Alertmanager webhook configuration",
         "fingerprint": "gmp-test-alert-12345",
         "annotations": {
           "summary": "GMP Webhook Test Alert",
           "description": "If you see this in Robusta, the webhook URL and credentials are working correctly!"
         },
         "labels": {
           "cluster_name": "external",
           "cluster": "external",
           "alertname": "GMP_WebhookTest",
           "severity": "warning",
           "namespace": "gmp-public",
           "source": "gmp-managed-alertmanager"
         }
       }
     ]
   }'

You should see the test alert in Robusta shortly after applying the resources or running the curl command.

