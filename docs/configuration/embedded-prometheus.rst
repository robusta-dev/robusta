Embedded Prometheus Stack
============================

Robusta can optionally install an embedded Prometheus stack with pre-configured alerts.

We provide defaults that were fine-tuned for low-noise and out-of-the-box integration with Robusta playbooks.

Default alerts were tested on the following clusters, to identify and remove false positives:

.. TODO: show table with testing results.

Alerts are based on excellent work done in the kubernetes-mixin project, with additional modifications by Robusta.

Enabling the Embedded Prometheus
-----------------------------------
By default, Robusta is installed without Prometheus and without default alerts. To enable them:

.. code-block:: yaml

    enablePrometheusStack: true

This setting is recommended if don't have Prometheus installed on your cluster.

Prometheus retention period
------------------------------
Robusta UI uses Prometheus data for showing graphs.
To keep storage usage low, Prometheus keeps the data only for 14-15 days.

To change how long Prometheus saves the data, set the retention in your `generated_values.yaml` file:

.. code-block:: yaml

      prometheus:
        prometheusSpec:
          retention: 15d

If you're not using Robusta's embedded Prometheus, refer to `the official Prometheus docs <https://prometheus.io/docs/prometheus/latest/storage/#operational-aspects>`_ for documentation on retention periods.
