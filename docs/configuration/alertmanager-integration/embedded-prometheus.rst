Embedded Prometheus Stack
============================

Robusta can install an embedded Prometheus stack with pre-configured alerts.

It includes defaults alerts that we fine-tuned in advance, as well as prebuilt Robusta playbooks.

This option is highly recommended, but disabled by default, as many users already have Prometheus installed.

To customize the bundled ``kube-prometheus-stack``, explore the chart `values.yaml <https://github.com/prometheus-community/helm-charts/blob/main/charts/kube-prometheus-stack/values.yaml>`_ file.

Enabling the Embedded Prometheus
-----------------------------------
Add to ``generated_values.yaml``:

.. code-block:: yaml

    enablePrometheusStack: true

Apply the change by performing a :ref:`Helm Upgrade <Simple Upgrade>`.

Change the retention period
------------------------------

By default, Prometheus stores data for 14-15 days.

You can modify retention times in ``generated_values.yaml``:

.. code-block:: yaml

      prometheus:
        prometheusSpec:
          retention: 15d #change the number of days here

Apply the change by performing a :ref:`Helm Upgrade <Simple Upgrade>`.


Grafana Persistent Data
------------------------------

To allow the Grafana dashboard to persist after the Grafana instance restarts, you could add to ``generated_values.yaml``:

.. code-block:: yaml

  ...
  # Customize settings
  kube-prometheus-stack:
    grafana:
      persistence:
        enabled: true

Apply the change by performing a :ref:`Helm Upgrade <Simple Upgrade>`.

Troubleshooting
---------------------

Encountering issues with your Prometheus? Follow this guide to resolve some :ref:`common errors <Common Errors>`.

