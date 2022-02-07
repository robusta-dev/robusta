Event Enrichment
####################################

The actions are used to gather extra data on errors, alerts, and other cluster events.

Use them as building blocks in your own automations.

Prometheus Enrichers
^^^^^^^^^^^^^^^^^^^^^^^^^

These actions enrich Prometheus alerts. They only work with the ``on_prometheus_alert`` trigger:

.. robusta-action:: playbooks.robusta_playbooks.alerts_integration.default_enricher

.. robusta-action:: playbooks.robusta_playbooks.alerts_integration.template_enricher

.. robusta-action:: playbooks.robusta_playbooks.alerts_integration.alert_definition_enricher

.. robusta-action:: playbooks.robusta_playbooks.alerts_integration.graph_enricher

.. robusta-action:: playbooks.robusta_playbooks.alerts_integration.stack_overflow_enricher


Prometheus Silencers
-----------------------

These actions can selectively silence Prometheus alerts. They only work with the ``on_prometheus_alert`` trigger:

.. robusta-action:: playbooks.robusta_playbooks.alerts_integration.severity_silencer

.. robusta-action:: playbooks.robusta_playbooks.alerts_integration.name_silencer

.. robusta-action:: playbooks.robusta_playbooks.alerts_integration.node_restart_silencer

Node Enrichers
^^^^^^^^^^^^^^^^^^^^^^^^^

These actions can add context to any node-related event, be it from ``on_prometheus_alert`` or ``on_node_update``.

.. robusta-action:: playbooks.robusta_playbooks.node_cpu_analysis.node_cpu_enricher

.. robusta-action:: playbooks.robusta_playbooks.node_enrichments.node_status_enricher

.. robusta-action:: playbooks.robusta_playbooks.node_enrichments.node_running_pods_enricher

.. robusta-action:: playbooks.robusta_playbooks.node_enrichments.node_allocatable_resources_enricher

.. robusta-action:: playbooks.robusta_playbooks.bash_enrichments.node_bash_enricher

Pod Enrichers
^^^^^^^^^^^^^^^^^^^^^^^^^

These actions can add context to any pod-related event, be it from ``on_prometheus_alert`` or ``on_pod_update``.

.. robusta-action:: playbooks.robusta_playbooks.alerts_integration.logs_enricher

.. robusta-action:: playbooks.robusta_playbooks.bash_enrichments.pod_bash_enricher

.. robusta-action:: playbooks.robusta_playbooks.pod_enrichments.pod_events_enricher

.. robusta-action:: playbooks.robusta_playbooks.pod_troubleshooting.pod_ps

Daemonset Enrichers
^^^^^^^^^^^^^^^^^^^^^^^^^

These actions can add context to any daemonset-related event, be it from ``on_prometheus_alert`` or ``on_daemonset_update``.

.. robusta-action:: playbooks.robusta_playbooks.daemonsets.daemonset_status_enricher

Deployment Enrichers
^^^^^^^^^^^^^^^^^^^^^^^^^

These actions can add context to any deployment-related event, be it from ``on_prometheus_alert`` or ``on_deployment_update``.

.. robusta-action:: playbooks.robusta_playbooks.deployment_enrichments.deployment_status_enricher

