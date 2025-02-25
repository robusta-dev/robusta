Enrich Alerts with Bash Scripts
#########################################

Robusta can add extra context to your Prometheus alerts, so you can respond to alerts faster.

In this tutorial, you will enrich an alert by running a bash script automatically.

Implementation
-----------------

When the ``CPUThrottlingHigh`` alert fires we can run ``ps aux`` to see which process has high CPU.

Add the following YAML to the ``customPlaybooks`` Helm value and :ref:`update Robusta <Simple Upgrade>`:

.. code-block:: yaml

   customPlaybooks:
   - triggers:
     - on_prometheus_alert:
         alert_name: CPUThrottlingHigh
     actions:
     - node_bash_enricher:
         bash_command: ps aux | head -n 5

Testing
--------------

Trigger the alert we defined by deploying a Pod that consumes a lot of CPU:

.. code-block:: bash

    kubectl apply -f https://raw.githubusercontent.com/robusta-dev/kubernetes-demos/main/cpu_throttling/throttling.yaml

Sample Alert
-----------------

.. image:: /images/custom_alert_with_bash_enrichment.png
  :width: 600
  :align: center


Further Reading
-----------------

* View all :ref:`Prometheus enrichment actions <Prometheus Enrichers>`
