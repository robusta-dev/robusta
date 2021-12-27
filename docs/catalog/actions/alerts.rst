.. _prometheus-alert-enrichment:

Prometheus Alert Enrichment
##################################

Introduction
--------------
Robusta has special features for handling Prometheus alerts in Kubernetes clusters including:

1. **Enrichers:** actions that enrich alerts with extra information based on the alert type
2. **Silencers:** actions that silence noisy alerts using more advanced methods than Prometheus/AlertManager's builtin silencing feature

When trying out these features, you can leave your existing alerting Slack channel in place and add a new channel for Robusta's improved Prometheus alerts.
This will let you compare Robusta's alerting with Prometheus' builtin alerting.

Each triggered action will add enrichment data to the finding.
After all the triggered actions are executed, the findings and enrichments will be sent to the configured sinks.

Configure Robusta
---------------------------------

.. admonition:: Configure Prometheus AlertManager

    Before you can enrich prometheus alerts, you must forward Prometheus alerts to Robusta by adding a webhook receiver to AlertsManager.

    See :ref:`Prometheus` for details.


Lets look at the simplest possible configuration in ``values.yaml`` which instructs Robusta to forward Prometheus alerts without any special enrichment:

.. code-block:: yaml

   builtinPlaybooks:
   - triggers:
     - on_prometheus_alert: {}
     actions:
     - default_enricher: {}


The above configuration isn't just forward prometheus alerts to the configured sinks.
We didn't add any special enrichment yet.
Below you can see how the default alert information looks in Slack:

.. image:: /images/default-slack-enrichment.png
  :width: 80 %
  :align: center

Adding an Enricher
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Now lets add an enricher to ``values.yaml`` which enriches the ``HostHighCPULoad`` alert:

.. code-block:: yaml

   builtinPlaybooks:
   - triggers:
     - on_prometheus_alert:
         alert_name: HostHighCpuLoad
     actions:
     - node_cpu_enricher: {}
   - triggers:
     - on_prometheus_alert: {}
     actions:
     - default_enricher: {}


When using the above yaml, all prometheus alerts are forwarded to the sinks unmodified except for the ``HostHighCPULoad``
alert which is enriched as you can see below.

Note that adding an enricher to a specific alert, doesn't stop other enrichers from running.
Enrichers will run by the order they appear in the values file.

It's highly recommended to always leave the ``default_enricher`` last, to add the default information to all alerts.

.. image:: /images/node-cpu-alerts-enrichment.png
  :width: 30 %
  :alt: Analysis of node cpu usage, breakdown by pods
.. image:: /images/node-cpu-treemap.svg
    :width: 30 %
.. image:: /images/node-cpu-usage-vs-request.svg
    :width: 30 %

Make sure to check out the full list of enrichers to see what you can add.


If for some reason, you would like to stop processing after some enricher, you can use the ``stop`` playbook parameter:

.. code-block:: yaml

   builtinPlaybooks:
   - triggers:
     - on_prometheus_alert:
         alert_name: HostHighCpuLoad
     actions:
     - node_cpu_enricher: {}
     stop: True
   - triggers:
     - on_prometheus_alert: {}
     actions:
     - default_enricher: {}

Using this configuration, the ``HostHighCpuLoad`` alert, will not include the default alert information.


Adding a Silencer
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Lets silence `KubePodCrashLooping` alerts in the first ten minutes after a node (re)starts:

.. code-block:: yaml

   builtinPlaybooks:
   - triggers:
     - on_prometheus_alert:
         alert_name: KubePodCrashLooping
     actions:
     - node_restart_silencer:
         post_restart_silence: 600 # seconds
   - triggers:
     - on_prometheus_alert: {}
     actions:
     - default_enricher: {}


Full example
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Here are all the above features working together:

.. code-block:: yaml

   builtinPlaybooks:
   - triggers:
     - on_prometheus_alert:
         alert_name: KubePodCrashLooping
     actions:
     - node_restart_silencer:
         post_restart_silence: 600 # seconds
   - triggers:
     - on_prometheus_alert:
         alert_name: HostHighCpuLoad
     actions:
     - node_cpu_enricher: {}
   - triggers:
     - on_prometheus_alert: {}
     actions:
     - default_enricher: {}


Available Enrichers
-----------------------

General Enrichers
^^^^^^^^^^^^^^^^^^^^^^^^^

.. robusta-action:: playbooks.robusta_playbooks.alerts_integration.default_enricher

.. robusta-action:: playbooks.robusta_playbooks.alerts_integration.template_enricher

.. robusta-action:: playbooks.robusta_playbooks.alerts_integration.logs_enricher

.. robusta-action:: playbooks.robusta_playbooks.alerts_integration.alert_definition_enricher

.. robusta-action:: playbooks.robusta_playbooks.alerts_integration.graph_enricher

Node Enrichers
^^^^^^^^^^^^^^^^^^^^^^^^^

.. robusta-action:: playbooks.robusta_playbooks.node_cpu_analysis.node_cpu_enricher

.. robusta-action:: playbooks.robusta_playbooks.oom_killer.oom_killer_enricher

.. robusta-action:: playbooks.robusta_playbooks.node_enrichments.node_status_enricher

.. robusta-action:: playbooks.robusta_playbooks.node_enrichments.node_running_pods_enricher

.. robusta-action:: playbooks.robusta_playbooks.node_enrichments.node_allocatable_resources_enricher

.. robusta-action:: playbooks.robusta_playbooks.bash_enrichments.node_bash_enricher

Pod Enrichers
^^^^^^^^^^^^^^^^^^^^^^^^^

.. robusta-action:: playbooks.robusta_playbooks.bash_enrichments.pod_bash_enricher

.. robusta-action:: playbooks.robusta_playbooks.cpu_throttling.cpu_throttling_analysis_enricher

.. robusta-action:: playbooks.robusta_playbooks.image_pull_backoff_enricher.image_pull_backoff_reporter

.. robusta-action:: playbooks.robusta_playbooks.pod_enrichments.pod_events_enricher

Daemonset Enrichers
^^^^^^^^^^^^^^^^^^^^^^^^^

.. robusta-action:: playbooks.robusta_playbooks.daemonsets.daemonset_status_enricher

.. robusta-action:: playbooks.robusta_playbooks.daemonsets.daemonset_misscheduled_analysis_enricher

Deployment Enrichers
^^^^^^^^^^^^^^^^^^^^^^^^^

.. robusta-action:: playbooks.robusta_playbooks.deployment_enrichments.deployment_status_enricher

Other Enrichers
^^^^^^^^^^^^^^^^^^^^^^^^^

.. robusta-action:: playbooks.robusta_playbooks.alerts_integration.stack_overflow_enricher

.. robusta-action:: playbooks.robusta_playbooks.alerts_integration.show_stackoverflow_search


Available Silencers
-----------------------

.. robusta-action:: playbooks.robusta_playbooks.alerts_integration.severity_silencer

.. robusta-action:: playbooks.robusta_playbooks.alerts_integration.name_silencer

.. robusta-action:: playbooks.robusta_playbooks.alerts_integration.node_restart_silencer

.. robusta-action:: playbooks.robusta_playbooks.daemonsets.daemonset_misscheduled_smart_silencer


