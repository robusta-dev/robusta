:orphan:

.. _define-alerts:

Define Custom Prometheus Alerts
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

Enable Global Rule Selection
*******************************
Before we add the rule itself, we should configure Kube-Prometheus-Stack to pickup all new alerts we place in the cluster.

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


Defining a Custom Alert
---------------------------------------

Prometheus Alerts are defined on Kubernetes using the PrometheusRule CRD.

As an example, we'll define an alert to find Pods with CPU usage over their request.

.. .. details:: What is the PrometheusRule CRD?

..     CRDs (Custom Resources Definitions) extend Kubernetes API with new resource types. You can apply and edit these
..     resources using ``kubectl`` just like Pods, Deployments, and other builtin resources.

..     The Prometheus Operator adds CRDs to Kubernetes so you can control Prometheus alerts with ``kubectl``. Whenever you
..     apply or edit a ``PrometheusRule`` CRD, the operator will update Prometheus's configuration automatically.

..     When Robusta's embedded Prometheus Stack is enabled, the Prometheus Operator is installed automatically.

Save the following YAML into a file and run `kubectl apply -f <filename>`

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
---------------------------------------

Deploy a pod that deliberately consumes a lot of CPU to trigger the alert we defined:

.. code-block:: bash

    kubectl apply -f https://raw.githubusercontent.com/robusta-dev/kubernetes-demos/main/cpu_throttling/throttling.yaml


You will know the alert was defined successfully when Prometheus fires an alert. When using Robusta, this means a notification will be received in all configured sinks.

## TODO image

.. image:: /images/highcputhrottling.png
  :width: 600
  :align: center

.. details:: How are Prometheus and Robusta alerts different?

    Prometheus and Robusta work a little differently. Prometheus alerts are based on thresholds and time periods,
    so it has built-in alerting delays to avoid false-positives. On the other hand, Robusta is event-driven and
    alerts based on discrete events. It notifies immediately without alerting delays and has rate-limiting features
    to avoid sending duplicate messages.

    When a Robusta playbook uses the ``on_prometheus_alert`` trigger, there is a delay on the Prometheus end before
    alerts ever reach Robusta. Once the alert reaches Robusta, the playbook executes immediately.

Next Steps
---------------

In the next tutorial, we enhance this Prometheus alert with Robusta. Keep reading to learn more:

* :ref:`Enrich Custom Prometheus Alerts`
