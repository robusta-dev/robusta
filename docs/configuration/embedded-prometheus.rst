Embedded Prometheus Stack
============================

Robusta can optionally install an embedded Prometheus stack with pre-configured alerts. Our goal is to provide defaults
that are fine-tuned for low-noise and out-of-the-box integration with Robusta playbooks.

This feature is disable by default. If you would like to enable it then set:

.. code-block:: yaml

    enablePrometheusStack: true

We recommend you enable this if haven't yet installed Prometheus on your cluster.

The alerts are based on excellent work already done by the kube-prometheus-stack project which itself takes
alerts from the kubernetes-mixin project.

Our alerting will likely diverge more over time as we take advantage of more Robusta features.

Prometheus retention period
------------------------------
Robusta UI uses Prometheus data for showing graphs.
To keep storage usage low, Prometheus keeps the data only for 14-15 days.

To change how long Prometheus saves the data, set the retention in your `generated_values.yaml` file:

.. code-block:: yaml

      prometheus:
        prometheusSpec:
          retention: 15d

If you're not using the embedded prometheus stack, click `here <https://prometheus.io/docs/prometheus/latest/storage/#operational-aspects>`_ to learn more.


See also
------------------------------

* :ref:`Robusta architecture <Standard Architecture>`
* `Comparison of Robusta and a bare-bones Prometheus stack without Robusta <https://home.robusta.dev/prometheus-based-monitoring/?from=docs>`_
