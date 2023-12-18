Enrich Custom Prometheus Alerts
#################################

.. In the last tutorial we defined a custom Prometheus alert.

Robusta can take your Prometheus alerts and add extra context to them, so you can respond to alerts faster and without digging elsewhere for information. In this tutorial, you will learn how to enrich alerts with two practical examples.


Custom Alert Enrichment Use Cases
-----------------------------------------
Let's explore practical use cases for custom alert enrichment


Use Case 1: Enrich Alerts by Running a Bash Script
*******************************************************
**Scenario**: You want to run a bash command to gather additonal information along with the alert.

**Prerequisites**:

* You must have some Prometheus alerts already defined. Ex: HostHighCpuLoad

**Implementation**:

Define a :ref:`customPlaybook <customPlaybooks>` that responds to our Prometheus alert.

Add the following YAML to the ``customPlaybooks`` Helm value:

.. code-block:: yaml

   customPlaybooks:
   - triggers:
     - on_prometheus_alert:
         alert_name: HostHighCpuLoad
     actions:
     - node_bash_enricher:
         bash_command: ps aux

Testing the Alert ## TODO Fix demo and add image
---------------------------------------------------
Deploy a pod that deliberately consumes a lot of CPU to trigger the alert we defined:

.. code-block:: bash

    kubectl apply -f https://raw.githubusercontent.com/robusta-dev/kubernetes-demos/main/cpu_throttling/throttling.yaml

We can wait for the alert to fire or we can speed things up and simulate the alert, as if it fired immediately:

.. code-block:: bash

    robusta demo-alert --alert=HostHighCpuLoad --labels=label1=test,label2=alert



Use Case 2:  Link Alerts to External Docs
*********************************************
**Scenario**: You want to add reference links along with your alert for your internal docs to provide exact steps to fix the issue.

**Prerequisites**:

* Kube-Prometheus-Stack installed with Robusta or seperately.
* Robusta installed and configured.
* Custom alert created following :ref:`Create Custom Alerting Rule <Creating a Custom Alerting Rule>` or any predefined alert.

**Implementation**:

Define a :ref:`customPlaybook <customPlaybooks>` that responds to our Prometheus alert:

Add the following YAML to the ``customPlaybooks`` Helm value:

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


Testing the Alert
---------------------------------------

Deploy a pod that deliberately consumes a lot of CPU to trigger the alert we defined:

.. code-block:: bash

    kubectl apply -f https://raw.githubusercontent.com/robusta-dev/kubernetes-demos/main/cpu_throttling/throttling.yaml

We can wait for the alert to fire or we can speed things up and simulate the alert, as if it fired immediately:

.. code-block:: bash

    robusta demo-alert --alert=KubeContainerCPURequestAlert --labels=label1=test,label2=alert

Once the alert fires, a notification arrives in your configured sinks.

**Sample Alert**:

.. image:: /images/custom-alert-with-reference-url.png
  :width: 600
  :align: center

.. warning::

    Defining a customPlaybook for a specific alert, wont stop other playbooks from seeing that alert too.

    Playbooks run in the order they appear in ``customPlaybooks``.

    To stop processing after some action, set the ``stop`` parameter:

    .. code-block:: yaml

       customPlaybooks:
       - triggers:
         - on_prometheus_alert:
             alert_name: HostHighCpuLoad
         actions:
         - node_cpu_enricher: {}
         stop: True
       - triggers:
         - on_prometheus_alert: {}
         actions:
         - some_other_action: {}

    Using this configuration, ``some_other_action`` wont run for ``HostHighCpuLoad``.

Further Reading
---------------

* View all :ref:`Prometheus enrichment actions <Prometheus Enrichers>`
