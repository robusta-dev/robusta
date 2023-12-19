Enrich Custom Prometheus Alerts
#################################

.. In the last tutorial we defined a custom Prometheus alert.

Robusta can add extra context to your Prometheus alerts, so you can respond to alerts faster and without digging elsewhere for information.

In this tutorial, you will learn how to enrich alerts with two practical use cases.

Use Case 1: Enrich Alerts by Running a Bash Script
*******************************************************

**Implementation**:

We will configure what bash command to run when an alert of your choosing fires. This is done using Robusta's :ref:`customPlaybook <customPlaybooks>`.

In the following example we use ``HostHighCpuLoad`` alert. Change this name

Add the following YAML to the ``customPlaybooks`` Helm value and :ref:`update Robusta <Simple Upgrade>`.

.. code-block:: yaml

   customPlaybooks:
   - triggers:
     - on_prometheus_alert:
         alert_name: HostHighCpuLoad
     actions:
     - node_bash_enricher:
         bash_command: ps aux

Testing the Alert ## TODO Fix demo and add image
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Deploy a pod that deliberately consumes a lot of CPU to trigger the alert we defined:

.. code-block:: bash

    kubectl apply -f https://raw.githubusercontent.com/robusta-dev/kubernetes-demos/main/cpu_throttling/throttling.yaml

We can wait for the alert to fire or we can speed things up and simulate the alert, as if it fired immediately:

.. code-block:: bash

    robusta demo-alert --alert=HostHighCpuLoad --labels=label1=test,label2=alert


Use Case 2: Link Alerts to External Docs
*********************************************

**Implementation**:

We will configure what additional information to send, when an alert of your choosing fires. This is done using Robusta's :ref:`customPlaybook <customPlaybooks>`.

In the following example we use ``KubeContainerCPURequestAlert`` created in the :ref:`Create Custom Alerting Rule <Creating a Custom Alerting Rule>` tutorial.

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


Testing the Alert
^^^^^^^^^^^^^^^^^^^^

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

.. .. warning::

..     Defining a customPlaybook for a specific alert, wont stop other playbooks from seeing that alert too.

..     Playbooks run in the order they appear in ``customPlaybooks``.

..     To stop processing after some action, set the ``stop`` parameter:

..     .. code-block:: yaml

..        customPlaybooks:
..        - triggers:
..          - on_prometheus_alert:
..              alert_name: HostHighCpuLoad
..          actions:
..          - node_cpu_enricher: {}
..          stop: True
..        - triggers:
..          - on_prometheus_alert: {}
..          actions:
..          - some_other_action: {}

..     Using this configuration, ``some_other_action`` wont run for ``HostHighCpuLoad``.

Further Reading
---------------

* View all :ref:`Prometheus enrichment actions <Prometheus Enrichers>`
