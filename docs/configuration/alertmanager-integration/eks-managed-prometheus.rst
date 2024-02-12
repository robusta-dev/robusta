AWS Managed Prometheus
*************************

This guide walks you through integrating your AWS Managed Prometheus with Robusta.

You'll need to configure two integrations: one to send alerts to Robusta and another to let Robusta query metrics and create silences. This guide only covers the integration to query metrics.

Configure Metric Querying
===============================

Metrics querying lets Robusta pull metrics from AWS Managed Prometheus.

1. Create an AWS access key, `See guide here <https://docs.aws.amazon.com/powershell/latest/userguide/pstools-appendix-sign-up.html>`_.

2. In your cluster, create a secret with your access key and secret access key, named `aws-secret-key`.

3. Collect the URL for your AWS Managed Prometheus workspace.

4. Append the following to your `generated_values.yaml` file.

.. code-block:: yaml

  globalConfig:
  ...
    prometheus_url: AWS_PROMETHEUS_URL

    # Create silences when using Grafana alerts (optional)
    # grafana_api_key: <YOUR GRAFANA EDITOR API KEY> # (1)
    # alertmanager_flavor: grafana

  runner:
    additional_env_vars:
    - name: PROMETHEUS_SSL_ENABLED
      value: "true"
    - name: AWS_ACCESS_KEY
      value: <ACCESS KEY HERE>
    - name: AWS_ACCESS_KEY
      valueFrom:
        secretKeyRef:
          name: aws-secret-key
          key: <NAME_OF_ACCESS_KEY_KEY>
    - name: AWS_SECRET_ACCESS_KEY
      valueFrom:
        secretKeyRef:
          name: aws-secret-key
          key: <NAME_OF_SECRET_ACCESS_KEY_KEY>
    - name: AWS_SERVICE_NAME
      value: "aps" # <SERVICE NAME HERE>, it is usually aps
    - name: AWS_REGION
      value: <REGION_OF_WORKSPACE_HERE>

.. code-annotations::
    1. This is necessary for Robusta to create silences when using Grafana Alerts, because of minor API differences in the AlertManager embedded in Grafana.

Optional Settings
==================

**Prometheus flags checks**

.. include:: ./_prometheus_flags_check.rst
