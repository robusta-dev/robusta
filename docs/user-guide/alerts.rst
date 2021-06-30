.. _prometheus-alert-enrichment:

Prometheus Alert Enrichment
##################################

Introduction
^^^^^^^^^^^^^^^
Robusta has special features for handling Prometheus alerts in Kubernetes clusters including:

1. **Enrichers:** playbooks that enrich alerts with extra information based on the alert type
2. **Silencers:** playbooks that silence noisy alerts using more advanced methods than Prometheus/AlertManager's builtin silencing feature

When trying out these features, you can leave your existing alerting Slack channel in place and add a new channel for Robusta's improved Prometheus alerts.
This will let you compare Robusta's alerting with Prometheus' builtin alerting.

These features are still in beta and therefore have been implemented differently than regular playbooks. To enable this mode
of operation, you configure a root ``alerts_integration`` playbook in ``active_playbooks.yaml`` and then add special enrichment
and silencer playbooks underneath that playbook. In the future, this functionality will likely be merged into regular playbooks.

Setup and configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^

Configure Prometheus AlertManager
----------------------------------
Before you can enrich prometheus alerts, you must forward Prometheus alerts to Robusta by adding a webhook receiver to AlertsManager.
See :ref:`Setting up the webhook` for details.

Configure Robusta
------------------------------
Lets look at the simplest possible ``active_playbooks.yaml`` which instructs Robusta to forward Prometheus alerts to Slack without any enrichment:

| **Enabling it:**

.. code-block:: yaml

   active_playbooks:
  - name: "alerts_integration"
    action_params:
      slack_channel: "robusta-alerts"

The above configuration isn't very useful because we haven't enriched any alerts yet.
However, we do get a minor aesthetic benefit because Robusta adds pretty formatting to alerts as you can see below:

.. image:: /images/default-slack-enrichment.png
  :width: 30 %
  :align: center

Adding an Enricher
-------------------
Now lets add an enricher to ``active_playbooks.yaml`` which enriches the ``HostHighCPULoad`` alert:

| **Enabling it:**

.. code-block:: yaml

   active_playbooks:
  - name: "alerts_integration"
    action_params:
      slack_channel: "robusta-alerts"
      alerts_config:
      - alert_name: "HostHighCpuLoad"
        enrichers:
        - name: "NodeCPUAnalysis"
        - name: "AlertDefaults"


When using the above yaml, all prometheus alerts are forwarded to Slack unmodified except for the ``HostHighCPULoad``
alert which is enriched as you can see below.

Note that adding an enricher to a specific alert always replaces the default enricher which is called ``AlertDefaults``.
Therefore, in the above example, we explicitly added back the ``AlertDefaults`` enricher to use both the default alert message and the enrichment.

.. image:: /images/node-cpu-alerts-enrichment.png
  :width: 30 %
  :alt: Analysis of node cpu usage, breakdown by pods
.. image:: /images/node-cpu-treemap.svg
    :width: 30 %
.. image:: /images/node-cpu-usage-vs-request.svg
    :width: 30 %

Make sure to check out the full list of enrichers to see what you can add.

Setting the default enricher
------------------------------

You can change the default enricher(s) for all alerts using the ``default_enrichers`` parameter.

.. code-block:: yaml

   active_playbooks:
  - name: "alerts_integration"
    action_params:
      slack_channel: "robusta-alerts"
      default_enrichers:
        - name: "AlertDefaults"

Adding a Silencer
-----------------
Now lets look at an example ``active_playbooks.yaml`` which silences KubePodCrashLooping alerts in the first ten minutes after a node (re)starts:

| **Enabling it:**

.. code-block:: yaml

   active_playbooks:
  - name: "alerts_integration"
    action_params:
      slack_channel: "robusta-alerts"
      alerts_config:
      - alert_name: "KubePodCrashLooping"
        silencers:
        - name: "NodeRestartSilencer"
          params:
            post_restart_silence: 600 # seconds

Full example
----------------
Here is an example which shows all the features discussed above working together:

.. code-block:: yaml

   active_playbooks:
  - name: "alerts_integration"
    action_params:
      slack_channel: "robusta-alerts"
      default_enrichers:
        - name: "AlertDefaults"
      alerts_config:
      - alert_name: "HostHighCpuLoad"
        enrichers:
        - name: "NodeCPUAnalysis"
      - alert_name: "KubeDeploymentReplicasMismatch"
        enrichers:
        - name: "SomeCustomEnricher"
        - name: "AlertDefaults" # adding alert defaults as well
      - alert_name: "KubePodCrashLooping"
        silencers:
        - name: "NodeRestartSilencer"
          params:
            post_restart_silence: 600 # seconds

Available enrichers
^^^^^^^^^^^^^^^^^^^^^^^^^^

**AlertDefaults:** send the alert message and labels to Slack

**NodeCPUAnalysis:** provide deep analysis of node cpu usage

**OOMKillerEnricher:** shows which pods were recently OOM Killed on a node

**GraphEnricher:** display a graph of the Prometheus query which triggered the alert

**StackOverflowEnricher:** add a button in Slack to search for the alert name on StackOverflow

**NodeRunningPodsEnricher:** add a list of the pods running on the node, with the pod Ready status

.. image:: /images/node-running-pods.png
  :width: 80 %
  :align: center

**NodeAllocatableResourcesEnricher:** add the allocatable resources available on the node

.. image:: /images/node-allocatable-resources.png
  :width: 80 %
  :align: center

Available Silencers
^^^^^^^^^^^^^^^^^^^^^^^^^^

**NodeRestartSilencer:** After a node is restarted, silence alerts for pods running on it.

| params: post_restart_silence, (seconds), default to 300

