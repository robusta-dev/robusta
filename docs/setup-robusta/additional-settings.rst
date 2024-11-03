:hide-toc:

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
     - node

If your alerts have different labels, you can change the mapping with the ``alertRelabel`` helm value.

A relabeling has 3 attributes:

* ``source``: Use the value from this label
* ``target``: This label will contain the value from ``source``
* ``operation``: Operation can be ``add`` (default) or ``replace``.

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

To correctly map your custom alert severity, you need to add ``custom_severity_map``. The values for each alert should be: high, medium, low, info, and debug.

For example:

.. code-block:: yaml

    globalConfig:
      custom_severity_map:
        devs_high: high
        ops_high: high
        devs_low: low


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

Pod logs gathered by Robusta can be censored using regexes. For example, a payment processing pod might have credit card numbers in its log. These can be sanitized in-cluster.

This feature applies to the following Robusta actions:

- :code:`logs_enricher`
- :code:`report_crash_loop`

To censor logs, define a `python regex <https://www.w3schools.com/python/python_regex.asp>`_ for expressions you wish to filter.

For example:

.. code-block:: yaml

    - logs_enricher:
        regex_replacement_style: SAME_LENGTH_ASTERISKS # You can also use NAMED
        regex_replacer_patterns:
          - name: MySecretPort
              regex: "my secret port \\d+"
          - name: UUID
              regex: "[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"

Given the following input:

.. code-block::

    # Input (actual pod log):
    2022-07-28 08:24:45.283 INFO     user's uuid: '193836d9-9cce-4df9-a454-c2edcf2e80e5'
    2022-07-28 08:35:00.762 INFO     Successfully loaded some critical module
    2022-07-28 08:35:01.090 INFO     using my secret port 114, ip: ['172.18.0.3']

The censored output will be:

.. code-block::

    # Output for SAME_LENGTH_ASTERISKS (How it will appear in Slack, for example):

    2022-07-28 08:24:45.283 INFO     user's uuid: '************************************'
    2022-07-28 08:35:00.762 INFO     Successfully loaded some critical module
    2022-07-28 08:35:01.090 INFO     using ******************, ip: ['172.18.0.3']

    # Output for NAMED (How it will appear in Slack, for example):

    2022-07-28 08:24:45.283 INFO     user's uuid: '[UUID]'
    2022-07-28 08:35:00.762 INFO     Successfully loaded some critical module
    2022-07-28 08:35:01.090 INFO     using [MySecretPort], ip: ['172.18.0.3']

It is best to define this in a :ref:`Global Config`, so it will be applied everywhere.

.. code-block:: yaml

    globalConfig: # Note: no need to specify logs_enricher or report_crash_loop by name here.
      regex_replacement_style: SAME_LENGTH_ASTERISKS
      regex_replacer_patterns:
        - name: MySecretPort
          regex: "my secret port \\d+"
        - name: UUID
          regex: "[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"

Place these values inside Robusta's Helm values and perform a :ref:`Helm Upgrade <Simple Upgrade>`.


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
