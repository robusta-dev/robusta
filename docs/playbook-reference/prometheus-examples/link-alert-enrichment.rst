Link Alerts to External Docs
#################################################

When troubleshooting production incidents, quick access to relevant documentation and runbooks is crucial!

This guide demonstrates how to link Prometheus alerts with external links to your technical documentation, GitHub repositories, and internal wikis.

Implementation
-----------------

In this example, we add links to the alert ``KubeContainerCPURequestAlert`` that we created in a :ref:`previous tutorial <Create Custom Prometheus Alerts>`.

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
    1. We're using custom emojis here that correspond to GitHub and Notion logos. Before you configure this, follow `this guide <https://slack.com/intl/en-gb/help/articles/206870177-Add-customised-emoji-and-aliases-to-your-workspace>`_ to add emojis to your workspace.


Testing
----------------

To test, deploy a resource-intensive pod to intentionally trigger the defined alert:

.. code-block:: bash

    kubectl apply -f https://raw.githubusercontent.com/robusta-dev/kubernetes-demos/main/cpu_throttling/throttling.yaml

We can wait for the alert to fire, or we can speed things up and simulate the alert, as if it fired immediately:

.. code-block:: bash

    robusta demo-alert --alert=KubeContainerCPURequestAlert --labels=label1=test,label2=alert

Once the alert fires, a notification will arrive with external links included.

Sample Alert
-------------------

.. image:: /images/custom-alert-with-reference-url.png
  :width: 600
  :align: center

Further Reading
-------------------

* View all :ref:`Prometheus enrichment actions <Prometheus Enrichers>`
