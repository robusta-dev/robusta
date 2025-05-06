Additional Settings
=======================

Global Config
--------------------------

The ``globalConfig`` Helm value defines global variables re-used across Robusta.

Robusta also expects several parameters to always be defined in ``globalConfig``:

cluster_name
    Unique for each cluster in your organization. Cluster Name be human-readable and need not be secret

account_id
    Keep secret! The Account ID uniquely identifies your cluster with Robusta cloud (if enabled). Should never be the
    same for different organizations. Together, ``cluster_name`` and ``account_id`` uniquely identify every cluster
    running Robusta in the world

signing_key
    Keep secret! The Signing Key is used to authenticate requests to run playbooks from outside the cluster (if enabled).

These values are generated automatically when setting up Robusta with the CLI. If you install Robusta on additional
clusters, make sure you change ``cluster_name`` accordingly. The other values should remain the same.

If you need to generate the secret values yourself, use cryptographically secure strings with at least 128 bits of
randomness.

Relabel Prometheus Alerts
-----------------------------

In order to enrich alerts, Robusta maps Prometheus alerts to related Kubernetes resources.

The following labels determine which Kubernetes resource relates to an alert:

.. list-table::
   :header-rows: 1

   * - Kubernetes Resource
     - Alert Labels
   * - Deployment
     - deployment, namespace
   * - DaemonSet
     - daemonset, namespace
   * - StatefulSet
     - statefulset, namespace
   * - Job
     - job_name, namespace
   * - Pod
     - pod, namespace
   * - HorizontalPodAutoscaler
     - horizontalpodautoscaler, namespace
   * - Node
     - node or instance (used as a fallback if node doesn't exist)

If your alerts have different labels, you can change the mapping with the ``alertRelabel`` helm value.

A relabeling has 3 attributes:

* ``source``: The label's name on your alerts (which differs from the expected value in the above table)
* ``target``: The standard label name that Robusta expects (a value from the table above)
* ``operation``: Either ``add`` (default) or ``replace``. If ``add``, your custom mapping will be recognized *in addition* to Robusta's default mapping.

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
------------------------------------

To help you prioritize alerts from different sources, Robusta maps alert severity to four standard levels:

* HIGH - requires your immediate attention - may indicate a service outage
* LOW - minor problems and areas for improvement (e.g. performance) - to be reviewed periodically on a weekly or bi-weekly cadence
* INFO - you probably want to be aware of these, but do not necessarily need to take action
* DEBUG - debug only - can be ignored unless you're actively debugging an issue

You are free to interpret these levels differently, but the above is a good starting point for most companies.

Prometheus alerts are normalized to the above levels as follows:

.. list-table::
  :header-rows: 1

  * - Prometheus Severity
    - Robusta Severity
  * - critical
    - HIGH
  * - high
    - HIGH
  * - medium
    - HIGH
  * - error
    - HIGH
  * - warning
    - LOW
  * - low
    - LOW
  * - info
    - INFO
  * - debug
    - DEBUG

Prometheus alerts with a severity **not in the above list** are mapped to Robusta's INFO level.

You can map your own Prometheus severities, using the ``custom_severity_map`` Helm value. For example:

.. code-block:: yaml

    globalConfig:
      custom_severity_map:
        # maps a p1 value on your own alerts to Robusta's HIGH value
        p1: high
        # maps a p2 value on your own alerts to Robusta's LOW value
        p2: low

The mapped values must be one of: high, low, info, and debug.

Two-way Interactivity
------------------------

Two-way interactivity allows the Robusta UI and the Slack sink to connect to the Robusta running in your cluster.

The Robusta UI uses interactivity to display dynamic data, such as Prometheus graphs.
Slack uses it to support custom remediation buttons.

To **enable** interactivity, set the following in your `generated_values.yaml` file:

.. code-block:: yaml

    disableCloudRouting: false

Censoring Logs
----------------

Pod logs gathered by Robusta can be censored using `Python regular expressions <https://www.w3schools.com/python/python_regex.asp>`_. For example, a payment processing pod might have credit card numbers or other sensitive information in its logs. These can be automatically sanitized before they appear in notifications.

**How to Enable Log Censoring for All Logs**

To censor sensitive information in all logs, add the following to your Helm values file:

.. code-block:: yaml

    globalConfig:
      regex_replacement_style: SAME_LENGTH_ASTERISKS  # Alternative: NAMED
      regex_replacer_patterns:
        - name: CreditCard
          regex: "[0-9]{4}[- ][0-9]{4}[- ][0-9]{4}[- ][0-9]{4}"
        - name: Email
          regex: "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}"
        - name: UUID
          regex: "[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"

After adding these values, perform a Helm upgrade:

.. code-block:: bash

    helm upgrade robusta robusta/robusta -f values.yaml

**Example: Before and After Censoring**

Given the following pod log:

.. code-block::

    # Original pod log:
    2022-07-28 08:24:45.283 INFO     user's uuid: '193836d9-9cce-4df9-a454-c2edcf2e80e5'
    2022-07-28 08:35:00.762 INFO     Customer email: user@example.com
    2022-07-28 08:35:01.090 INFO     Payment processed with card: 4111-1111-1111-1111

The censored output will appear as:

.. code-block::

    # Using SAME_LENGTH_ASTERISKS style:
    2022-07-28 08:24:45.283 INFO     user's uuid: '************************************'
    2022-07-28 08:35:00.762 INFO     Customer email: ****************
    2022-07-28 08:35:01.090 INFO     Payment processed with card: *******************

    # Using NAMED style:
    2022-07-28 08:24:45.283 INFO     user's uuid: '[UUID]'
    2022-07-28 08:35:00.762 INFO     Customer email: [Email]
    2022-07-28 08:35:01.090 INFO     Payment processed with card: [CreditCard]

**Note:** This censoring applies to logs displayed in Robusta's built-in notifications, including those shown by the following Robusta actions:

- :code:`logs_enricher` - Shows container logs in various alerts
- :code:`report_crash_loop` - Shows container logs for crashing pods

For specific actions, you can also override these settings in your playbook definitions if needed.


Memory allocation on big clusters
------------------------------------

On bigger clusters, increase Robusta's memory ``requests`` and ``limits``

Add this to Robusta's Helm values:

.. code-block:: yaml

        runner:
          resources:
            requests:
              memory: 2048Mi
            limits:
              memory: 2048Mi

Adding a Cluster Label to Alerts
---------------------------------------------
When using the built-in Prometheus stack, Robusta uses the ``cluster_name`` you set during installation to identify which alerts belong to which cluster.

If you forward external alerts to Robusta (e.g., from Grafana/Grafana Cloud), you will need to pass the ``cluster_name`` metadata manually. For example, if you use Grafana alerting, ensure that all your metrics and alerts have a ``cluster_name`` label.

The easiest way to do this with Prometheus is by setting `metric_relabel_configs <https://prometheus.io/docs/prometheus/latest/configuration/configuration/#metric_relabel_configs>`_. How you apply that configuration depends on how Prometheus was installed. If you use kube-prometheus-stack, there is a Helm value for it:

.. code-block:: yaml

    prometheus:
      prometheusSpec:
        additionalScrapeConfigs:
          - job_name: "cluster-name-to-metric"
            kubernetes_sd_configs:
              - role: pod
            metric_relabel_configs:
              - target_label: cluster_name
                replacement: "YOUR_ROBUSTA_CLUSTER_NAME" # This is the cluster name you set in the Helm values during Robusta installation

.. note:: 
  
  1. ``cluster_name`` label will be added only to metrics after you add this config. i.e Previously scraped metrics will not have ``cluster_name`` label. **You will need to wait a few hours after adding this configuration for the label to show up on your alerts and be forwarded correctly.**
  2. ``prometheus.prometheusSpec.externalLabels.cluster`` does not work for cases when you need ``cluster_name`` label in Grafana.
 