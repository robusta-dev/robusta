Event Enrichment
####################################

The actions are used to gather extra data on errors, alerts, and other cluster events.

Use them as building blocks in your own automations.

Node Enrichers
^^^^^^^^^^^^^^^^^^^^^^^^^

These actions can add context to any node-related event, be it from ``on_prometheus_alert`` or ``on_node_update``.

.. robusta-action:: playbooks.robusta_playbooks.bash_enrichments.node_bash_enricher

.. robusta-action:: playbooks.robusta_playbooks.node_enrichments.node_status_enricher

.. robusta-action:: playbooks.robusta_playbooks.node_enrichments.node_running_pods_enricher

.. robusta-action:: playbooks.robusta_playbooks.node_enrichments.node_allocatable_resources_enricher

.. robusta-action:: playbooks.robusta_playbooks.node_enrichments.node_graph_enricher

.. robusta-action:: playbooks.robusta_playbooks.node_cpu_analysis.node_cpu_enricher

Pod Enrichers
^^^^^^^^^^^^^^^^^^^^^^^^^

These actions can add context to any pod-related event, be it from ``on_prometheus_alert`` or ``on_pod_update``.

.. robusta-action:: playbooks.robusta_playbooks.alerts_integration.logs_enricher on_pod_crash_loop

.. robusta-action:: playbooks.robusta_playbooks.event_enrichments.pod_events_enricher

.. robusta-action:: playbooks.robusta_playbooks.bash_enrichments.pod_bash_enricher
    :trigger-params: {"alert_name": "ExampleLowDiskAlert"}

.. robusta-action:: playbooks.robusta_playbooks.pod_enrichments.pod_graph_enricher

.. robusta-action:: playbooks.robusta_playbooks.pod_enrichments.pod_node_graph_enricher

.. robusta-action:: playbooks.robusta_playbooks.pod_troubleshooting.pod_ps

.. robusta-action:: playbooks.robusta_playbooks.oom_killer.pod_oom_killer_enricher

Daemonset Enrichers
^^^^^^^^^^^^^^^^^^^^^^^^^

These actions can add context to any daemonset-related event, be it from ``on_prometheus_alert`` or ``on_daemonset_update``.

.. robusta-action:: playbooks.robusta_playbooks.daemonsets.daemonset_status_enricher

Deployment Enrichers
^^^^^^^^^^^^^^^^^^^^^^^^^

These actions can add context to any deployment-related event, be it from ``on_prometheus_alert`` or ``on_deployment_update``.

.. robusta-action:: playbooks.robusta_playbooks.deployment_enrichments.deployment_status_enricher

.. robusta-action:: playbooks.robusta_playbooks.event_enrichments.deployment_events_enricher

Job Enrichers
^^^^^^^^^^^^^^^^^^^^^^^^^

These actions can add context to any job-related event, be it from ``on_prometheus_alert`` or ``on_job_update``.

.. robusta-action:: playbooks.robusta_playbooks.job_actions.job_events_enricher

.. robusta-action:: playbooks.robusta_playbooks.job_actions.job_info_enricher

.. robusta-action:: playbooks.robusta_playbooks.job_actions.job_pod_enricher

Kubernetes Resource Enrichers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

These actions can add context to more than one Kubernetes resource type

.. robusta-action:: playbooks.robusta_playbooks.k8s_resource_enrichments.related_pods

.. robusta-action:: playbooks.robusta_playbooks.k8s_resource_enrichments.list_resource_names

.. robusta-action:: playbooks.robusta_playbooks.k8s_resource_enrichments.get_resource_yaml

Event Enrichers
^^^^^^^^^^^^^^^^^^^^^^^^^

.. robusta-action:: playbooks.robusta_playbooks.event_enrichments.event_resource_events

.. robusta-action:: playbooks.robusta_playbooks.event_enrichments.deployment_events_enricher

.. robusta-action:: playbooks.robusta_playbooks.event_enrichments.pod_events_enricher

Prometheus Enrichers
^^^^^^^^^^^^^^^^^^^^^^^^^

These actions enrich Prometheus alerts and only support the ``on_prometheus_alert`` trigger.

However, the opposite is not true! ``on_prometheus_alert`` supports many actions, not just these.

.. robusta-action:: playbooks.robusta_playbooks.alerts_integration.graph_enricher

.. robusta-action:: playbooks.robusta_playbooks.alerts_integration.custom_graph_enricher

.. robusta-action:: playbooks.robusta_playbooks.alerts_integration.alert_graph_enricher

.. robusta-action:: playbooks.robusta_playbooks.alerts_integration.template_enricher

.. robusta-action:: playbooks.robusta_playbooks.alerts_integration.stack_overflow_enricher

.. robusta-action:: playbooks.robusta_playbooks.alerts_integration.default_enricher

.. robusta-action:: playbooks.robusta_playbooks.alerts_integration.alert_definition_enricher

Prometheus Silencers
^^^^^^^^^^^^^^^^^^^^^^^^^

These actions can selectively silence Prometheus alerts. They only work with the ``on_prometheus_alert`` trigger:

.. robusta-action:: playbooks.robusta_playbooks.alerts_integration.node_restart_silencer

.. robusta-action:: playbooks.robusta_playbooks.alerts_integration.severity_silencer

.. robusta-action:: playbooks.robusta_playbooks.alerts_integration.name_silencer

.. robusta-action:: playbooks.robusta_playbooks.alerts_integration.silence_alert

.. robusta-action:: playbooks.robusta_playbooks.alerts_integration.pod_status_silencer
