:orphan:

.. _define-alerts:

Create Custom Prometheus Alerts
##############################################

You can define new alerts in two ways using Robusta:

1. Prometheus Alerts - Using PromQL
2. Robusta Playbooks - Using :ref:`customPlaybooks YAML <What are Playbooks?>`

These methods are not mutually exclusive. Robusta playbooks can respond to Prometheus alerts, or they can generate
alerts themselves by listening directly to the Kubernetes APIServer. To better understand the trade-offs, refer to
:ref:`Should I generate alerts with Robusta or with Prometheus? <robusta-or-prometheus-alerts>`

In this tutorial, we use the first method to generate a custom Prometheus alert using PromQL. In the next tutorial,
we define a custom Robusta playbook that enhances the alert and makes it better.

Prerequisites
--------------

* Kube-Prometheus-Stack, installed via Robusta or seperately.
* Enable global rule selection for the Prometheus operator. Add the following config to your ``generated_values.yaml``. (By default Prometheus Operator picks up only certain new alerts, here we tell it to pick up all new alerts)

  .. grid-item::

      .. md-tab-set::

          .. md-tab-item:: Robusta Prometheus

            .. code-block:: yaml

              kube-prometheus-stack:
                prometheus:
                  prometheusSpec:
                    ruleNamespaceSelector: {} # (1)
                    ruleSelector: {} # (2)
                    ruleSelectorNilUsesHelmValues: false # (3)

            .. code-annotations::
              1. Add a namespace if you want Prometheus to identify rules created in specific namespaces. Leave ``{}`` to detect rules from any namespace.
              2. Add a label if you want Prometheus to detect rules with a specific selector. Leave ``{}`` to detect rules with any label.
              3. When set to `false`, Prometheus detects rules that are created directly, not just rules created using helm values file.

          .. md-tab-item:: Other Prometheus

            .. code-block:: yaml

              prometheus:
                prometheusSpec:
                  ruleNamespaceSelector: {} # (1)
                  ruleSelector: {} # (2)
                  ruleSelectorNilUsesHelmValues: false # (3)

            .. code-annotations::
              1. Add a namespace if you want Prometheus to identify rules created in specific namespaces. Leave ``{}`` to detect rules from any namespace.
              2. Add a label if you want Prometheus to detect rules with a specific selector. Leave ``{}`` to detect rules with any label.
              3. When set to `false`, Prometheus detects rules that are created directly, not just rules created using helm values file.

Creating a Custom Alert
---------------------------------------

Prometheus Alerts are defined on Kubernetes using the PrometheusRule CRD.

As an example, we'll define an alert to find Pods with CPU usage over their request.

Save the following YAML into ``my_alert.yaml`` and run ``kubectl apply -f my_alert.yaml``

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

Testing the Alert
-----------------------------

To test the alert, deploy a pod that uses more CPU than its request.

.. code-block:: bash

    kubectl apply -f https://raw.githubusercontent.com/robusta-dev/kubernetes-demos/main/cpu_throttling/throttling.yaml

You will know the alert was defined successfully when Prometheus fires an alert. When using Robusta, this means a notification will be received in all configured sinks.

.. image:: /images/container_cpu_request_alert.png
  :width: 600
  :align: center

Next Steps
---------------

Learn how to enrich Prometheus alerts with more context, so that you can respond faster:

* :ref:`Prometheus Alert Enrichment`
