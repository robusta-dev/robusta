Enrich Custom Prometheus Alerts
#################################

Robusta can add extra context to your Prometheus alerts, so you can respond to alerts faster and without digging elsewhere for information.

In this tutorial, you will learn how to enrich alerts with two practical use cases.

Use Case 1: Enrich Alerts by Running a Bash Script
*******************************************************

**Implementation**:

Add the following YAML to the ``customPlaybooks`` Helm value and :ref:`update Robusta <Simple Upgrade>`. This configures Robusta to execute the ``ps aux`` command in response to the ``HostHighCpuLoad`` alert.

.. code-block:: yaml

   customPlaybooks:
   - triggers:
     - on_prometheus_alert:
         alert_name: CPUThrottlingHigh
     actions:
     - node_bash_enricher:
         bash_command: ps aux

**Testing**:

Trigger the alert we defined by deploying a Pod that consumes a lot of CPU:

.. code-block:: bash

    kubectl apply -f https://raw.githubusercontent.com/robusta-dev/kubernetes-demos/main/cpu_throttling/throttling.yaml

We can wait for the alert to fire or we can speed things up and simulate the alert, as if it fired immediately:

.. code-block:: bash

    robusta demo-alert --alert=HostHighCpuLoad --labels=label1=test,label2=alert


Use Case 2: Enhance Alerts with Links to External Documentation
***********************************************************************

**Implementation**:

Add external links to your alerts, like documentation pages. In this example, we add links to the alert ``KubeContainerCPURequestAlert`` that we created in a previous tutorial.

Add the following YAML to the ``customPlaybooks`` Helm value and :ref:`update Robusta <Simple Upgrade>`.

.. code-block:: yaml

  customPlaybooks:
  - triggers:
    - on_prometheus_alert:
        alert_name: KubeContainerCPURequestAlert
    actions:
    - custom_graph_enricher:
        graph_title: CPU Usage for this container
        graph_duration_minutes: 5
        chart_values_format: Plain
        promql_query: 'sum(rate(container_cpu_usage_seconds_total{container="stress"}[5m])) by (pod)'
    - template_enricher:
        template: | # (1)
          :scroll: Playbook <https://playbook-url/|Handling High Resource Utilization>
          :github: Adjust CPU requests <https://github.com/YourRepository/|in the `Prod-sre` repository>
          :notion: Internal Docs on <https://notion.com/path-to-docs/|Customizing CPU requests>

.. code-annotations::
    1. Before you add a custom Slack emoji follow `this guide <https://slack.com/intl/en-gb/help/articles/206870177-Add-customised-emoji-and-aliases-to-your-workspace>`_ to add them your workspace.


**Testing**:

To test, deploy a resource-intensive pod to intentionally trigger the defined alert:

.. code-block:: bash

    kubectl apply -f https://raw.githubusercontent.com/robusta-dev/kubernetes-demos/main/cpu_throttling/throttling.yaml

We can wait for the alert to fire or we can speed things up and simulate the alert, as if it fired immediately:

.. code-block:: bash

    robusta demo-alert --alert=KubeContainerCPURequestAlert --labels=label1=test,label2=alert

Once the alert fires, a notification will arrive with external links included.

**Sample Alert**:

.. image:: /images/custom-alert-with-reference-url.png
  :width: 600
  :align: center

Further Reading
*********************

* View all :ref:`Prometheus enrichment actions <Prometheus Enrichers>`
