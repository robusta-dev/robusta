.. _prometheus-alert-enrichment:

Prometheus Alert Enrichment
##################################

Introduction
^^^^^^^^^^^^^^^
Robusta has a number of special features for handling Prometheus alerts in Kubernetes clusters. The primary two features are:

1. Enriching alerts with extra data, graphs, and analysis that is specific to the alert type
2. Silencing noisy alerts with advanced methods beyond what Prometheus/AlertManager does out of the box

To enable these features, you configure a special playbook which forwards all Prometheus alerts to Slack. Each alert can be
enriched, silenced, or (by default) passed through to Slack without modification.

These features are still in beta and therefore have been implemented differently than regular playbooks. To enable this mode
of operation, you configure a root ``alerts_integration`` playbook in ``active_playbooks.yaml`` and then add special enrichment
and silencer playbooks underneath that playbook. In the future, this functionality will likely be merged into regular playbooks.

Alert Manager Configuration
---------------------
In order to forward Prometheus alerts to Robusta first add a receiver to Alerts Manager. See :ref:`Setting up the webhook` for details.

Examples
^^^^^^^^^^
Lets look at an example ``active_playbooks.yaml`` file and then we'll see in more detail how to configure it.

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


When using the above yaml, all prometheus alerts are forwarded to Slack unmodified except for the ``HostHighCPULoad``
alert which is enriched as you can see below:

.. image:: /images/node-cpu-alerts-enrichment.png
  :width: 800
  :align: center
  :alt: Analysis of node cpu usage, breakdown by pods

.. image:: /images/node-cpu-treemap.svg
    :width: 40 %
.. image:: /images/node-cpu-usage-vs-request.svg
    :width: 40 %

Configuration
^^^^^^^^^^^^^

Here is a more advanced example which shows all the functionality supported:

.. code-block:: yaml

   active_playbooks:
  - name: "alerts_integration"
    action_params:
      slack_channel: "robusta-alerts"
      default_enricher: "AlertDefaults"
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

A few explanations:

1. Adding an enricher to a specific alert will replace the default enricher. In case you want both, explicitly add the ``AlertDefaults`` enricher as well.

2. In order to add custom enrichment to **all** alerts, you can specify the ``default_enricher`` parameter in the yaml. This is optional and if defined overrides the builtin default

Available enrichers
^^^^^^^^^^^^^^^^^^^^^^^^^^

**NodeCPUAnalysis:** provide deep analysis of node cpu usage

Available Silencers
^^^^^^^^^^^^^^^^^^^^^^^^^^

**NodeRestartSilencer:** After a node is restarted, silence alerts for pods running on it.
| params: post_restart_silence, (seconds), default to 300

