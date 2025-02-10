Enrich Alerts with Bash Scripts
#########################################

Robusta can add extra context to your Prometheus alerts, so you can respond to alerts faster.

In this tutorial, you will learn how to enrich alerts by running a bash script when the alert fires.

Implementation
-----------------

Add the following YAML to the ``customPlaybooks`` Helm value and :ref:`update Robusta <Simple Upgrade>`. This configures Robusta to execute the ``ps aux`` command in response to the ``CPUThrottlingHigh`` alert.

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
