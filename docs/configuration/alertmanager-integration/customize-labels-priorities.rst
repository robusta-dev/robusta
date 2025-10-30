Customize Labels and Priorities
=================================

Relabel Prometheus Alerts
--------------------------

When sending Prometheus alerts to Robusta, alerts are mapped onto related Kubernetes resources, when possible. This mapping relies on the alerts having the following labels:

+---------------------------+-------------------------------------------+
| Kubernetes Resource       | Alert Labels                              |
+===========================+===========================================+
| Deployment                | deployment, namespace                     |
+---------------------------+-------------------------------------------+
| DaemonSet                 | daemonset, namespace                      |
+---------------------------+-------------------------------------------+
| StatefulSet               | statefulset, namespace                    |
+---------------------------+-------------------------------------------+
| Job                       | job_name, namespace                       |
+---------------------------+-------------------------------------------+
| Pod                       | pod, namespace                            |
+---------------------------+-------------------------------------------+
| HorizontalPodAutoscaler   | horizontalpodautoscaler, namespace        |
+---------------------------+-------------------------------------------+
| Node                      | node or instance (fallback if node        |
|                           | doesn't exist)                            |
+---------------------------+-------------------------------------------+

If your alerts have different labels, you can change the mapping with the ``alertRelabel`` helm value.

A relabeling has 3 attributes:

* ``source``: The label's name on your alerts (which differs from the expected value in the above table)
* ``target``: The standard label name that Robusta expects (a value from the table above)
* ``operation``: Either ``add`` (default) or ``replace``. If ``add``, your custom mapping will be recognized in addition to Robusta's default mapping.

For example:

.. code-block:: yaml

    alertRelabel:
      - source: "pod_name"
        target: "pod"
        operation: "add"
      - source: "deployment_name"
        target: "deployment"
        operation: "replace"
      - source: "job_name"
        target: "job"

Mapping Custom Alert Severity
------------------------------

To help you prioritize alerts from different sources, Robusta maps alert severity to four standard levels:

* **HIGH** - requires your immediate attention - may indicate a service outage
* **LOW** - minor problems and areas for improvement (e.g. performance) - to be reviewed periodically on a weekly or bi-weekly cadence
* **INFO** - you probably want to be aware of these, but do not necessarily need to take action
* **DEBUG** - debug only - can be ignored unless you're actively debugging an issue

You are free to interpret these levels differently, but the above is a good starting point for most companies.

Prometheus alerts are normalized to the above levels as follows:

+----------------------+--------------------+
| Prometheus Severity  | Robusta Severity   |
+======================+====================+
| critical             | HIGH               |
+----------------------+--------------------+
| high                 | HIGH               |
+----------------------+--------------------+
| medium               | HIGH               |
+----------------------+--------------------+
| error                | HIGH               |
+----------------------+--------------------+
| warning              | LOW                |
+----------------------+--------------------+
| low                  | LOW                |
+----------------------+--------------------+
| info                 | INFO               |
+----------------------+--------------------+
| debug                | DEBUG              |
+----------------------+--------------------+

Prometheus alerts with a severity not in the above list are mapped to Robusta's INFO level.

You can map your own Prometheus severities, using the ``custom_severity_map`` Helm value. For example:

.. code-block:: yaml

    globalConfig:
      custom_severity_map:
        # maps a p1 value on your own alerts to Robusta's HIGH value
        p1: high
        # maps a p2 value on your own alerts to Robusta's LOW value
        p2: low

The mapped values must be one of: ``high``, ``low``, ``info``, and ``debug``.
