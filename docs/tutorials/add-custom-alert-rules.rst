Creating a Custom Alerting Rule
=================================
Alerting Rules are a type of Prometheus rules used to send alerts based on a predefined PromQL expression. .... How are they useful?

To create a custom alert on Kube-Prometheus-Stack we use the ``PrometheusRule`` CRD. First we will update Prometheus to recognize rules which are added directly as Custom Resources.

Enable Global Rule Selection
--------------------------------
Before we add the rule itself, we should configure Kube-Prometheus-Stack to identify alerts that are created without using helm values.
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

Create the PrometheusRule
-------------------------------
Save the following YAML code into a called newrule.yaml and run ``kubectl apply -f newrule.yaml``

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

You should receive an alert when the Prometheus expression is matched.
