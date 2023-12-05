Enrich Custom Prometheus Alerts
#################################

.. In the last tutorial we defined a custom Prometheus alert.

We now configure a Robusta playbook to enhance a Prometheus alert.

Prerequisites
---------------------------------
You must have some Prometheus alerts already defined. Ex: HostHighCpuLoad

Custom Alert Enrichment Use Cases
-----------------------------------------
Let's explore practical use cases for custom alert enrichment


Use Case 1: Run a Bash Script When Alert is Fired
*******************************************************
**Scenario**: You want to run a bash command to gather additonal information along with the alert.

**Implementation**:

Define a :ref:`customPlaybook <customPlaybooks>` that responds to our Prometheus alert:

Add the following YAML to the ``customPlaybooks`` Helm value:

.. code-block:: yaml

   customPlaybooks:
   - triggers:
     - on_prometheus_alert:
         alert_name: HostHighCpuLoad
     actions:
     - node_bash_enricher:
         bash_command: ps aux


Use Case 2: Add References URL's for Docs/Websites/Applications
******************************************************************
**Scenario**: You want to add reference links along with your alert for your internal docs to provide exact steps to fix the issue.

**Implementation**:

Creating a Custom Alert
============================

First we will create a custom alert and add it to Prometheus. You can skip this step if you already have an alert.

To create a custom alert on Kube-Prometheus-Stack we use the ``PrometheusRule`` CRD. First we will update Prometheus to recognize rules which are added directly as Custom Resources.

Add the following config to your Robusta generated_values.yaml if you are using kube-prometheus-stack installed by Robusta. Otherwise remove ``kube-prometheus-stack:`` and add the config to your values file.

.. code-block:: yaml

    kube-prometheus-stack:
      prometheus:
        ruleNamespaceSelector: {} # (1)
        ruleSelector: {} # (2)
        ruleSelectorNilUsesHelmValues: false # (3)

.. code-annotations::
    1. Add a namespace if you want Prometheus to identify rules created in specific namespaces. Leave ``{}`` to detect rules from any namespace.
    2. Add a label if you want Prometheus to detect rules with a specific selector. Leave ``{}`` to detect rules with any label.
    3. When set to `false`, Prometheus detects rules that are created directly, not just rules created using values helm values file.

Create a PrometheusRule and add your alert.

.. code-block:: yaml

  apiVersion: monitoring.coreos.com/v1
  kind: PrometheusRule
  metadata:
    name: container-cpu-alert
    labels:
      prometheus: kube-prometheus
      role: alert-rules
  spec:
    groups:
      - name: container-cpu-usage
        rules:
          - alert: KubeContainerCPURequestAlert
            expr: |
              (rate(container_cpu_usage_seconds_total{container="stress"}[5m]) /
              on (container) kube_pod_container_resource_requests{resource="cpu", container="stress"}) > 0.75
            for: 1m
            labels:
              severity: warning
            annotations:
              summary: "Container CPU usage is above 75% of request for 5 minutes"
              description: "The container is using more than 75% of its requested CPU for 5 minutes."

Add Reference URL's
=======================

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
        template: |
          :scroll: Playbook <https://playbook-url/|Handling High Resource Utilization>
          :github: Adjust CPU requests <https://github.com/YourRepository/|in the `Prod-sre` repository>
          :notion: Internal Docs on <https://notion.com/path-to-docs/|Customizing CPU requests>


**Note**: You should add `custom slack emoji's <https://slack.com/intl/en-gb/help/articles/206870177-Add-customised-emoji-and-aliases-to-your-workspace>`_ to your work space before adding emoji's to your alerts.

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
