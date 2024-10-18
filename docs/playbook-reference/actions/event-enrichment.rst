Event Enrichment
####################################

The actions are used to gather extra data on errors, alerts, and other cluster events.

Use them as building blocks in your own automations, or write :ref:`your own enrichment actions in Python <Developing New Actions>`.

Node Enrichers
^^^^^^^^^^^^^^^^^^^^^^^^^

These actions can add context to any node-related event, be it from ``on_prometheus_alert`` or ``on_node_update``.

.. robusta-action:: playbooks.robusta_playbooks.bash_enrichments.node_bash_enricher

.. robusta-action:: playbooks.robusta_playbooks.node_enrichments.node_status_enricher

.. robusta-action:: playbooks.robusta_playbooks.node_enrichments.node_running_pods_enricher

.. robusta-action:: playbooks.robusta_playbooks.node_enrichments.node_allocatable_resources_enricher

.. robusta-action:: playbooks.robusta_playbooks.node_enrichments.node_graph_enricher

.. robusta-action:: playbooks.robusta_playbooks.node_cpu_analysis.node_cpu_enricher

.. .. robusta-action:: playbooks.robusta_playbooks.node_enrichments.node_health_watcher

Pod Enrichers (General)
^^^^^^^^^^^^^^^^^^^^^^^^^

These actions can add context to any pod-related event, be it from ``on_prometheus_alert`` or ``on_pod_update``.

.. robusta-action:: playbooks.robusta_playbooks.alerts_integration.logs_enricher
    :recommended-trigger: on_pod_crash_loop

.. robusta-action:: playbooks.robusta_playbooks.event_enrichments.pod_events_enricher

.. robusta-action:: playbooks.robusta_playbooks.bash_enrichments.pod_bash_enricher
    :trigger-params: {"alert_name": "ExampleLowDiskAlert"}

.. robusta-action:: playbooks.robusta_playbooks.pod_enrichments.pod_graph_enricher

.. robusta-action:: playbooks.robusta_playbooks.pod_enrichments.pod_node_graph_enricher

.. robusta-action:: playbooks.robusta_playbooks.pod_troubleshooting.pod_ps

.. robusta-action:: playbooks.robusta_playbooks.image_pull_backoff_enricher.image_pull_backoff_reporter


Pod Enrichers (Crashes)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


These actions add context for specific Pod-related errors.

They're less general than the above actions, and usually designed for a specific error like CrashLoopBackOff.

.. robusta-action:: playbooks.robusta_playbooks.restart_loop_reporter.report_crash_loop

.. deprecated
.. .. robusta-action:: playbooks.robusta_playbooks.restart_loop_reporter.restart_loop_reporter

.. robusta-action:: playbooks.robusta_playbooks.oom_killer.pod_oom_killer_enricher
    :recommended-trigger: on_pod_oom_killed

.. .. robusta-action:: playbooks.robusta_playbooks.image_pull_backoff_enricher.image_pull_backoff_reporter

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

These actions are for use with :ref:`on_kubernetes_warning_event_create` and other Warning Event triggers.

For actions that *fetch* Warning Events for other triggers, see :ref:`job_events_enricher`, :ref:`pod_events_enricher`, and :ref:`deployment_events_enricher`

.. robusta-action:: playbooks.robusta_playbooks.event_enrichments.event_resource_events

Prometheus Enrichers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

These actions enrich Prometheus alerts and only support the :ref:`on_prometheus_alert` trigger.

.. robusta-action:: playbooks.robusta_playbooks.alerts_integration.graph_enricher

.. robusta-action:: playbooks.robusta_playbooks.alerts_integration.custom_graph_enricher

.. robusta-action:: playbooks.robusta_playbooks.alerts_integration.alert_graph_enricher

.. robusta-action:: playbooks.robusta_playbooks.alerts_integration.template_enricher

.. robusta-action:: playbooks.robusta_playbooks.alerts_integration.stack_overflow_enricher

.. robusta-action:: playbooks.robusta_playbooks.alerts_integration.default_enricher

.. robusta-action:: playbooks.robusta_playbooks.alerts_integration.foreign_logs_enricher

.. robusta-action:: playbooks.robusta_playbooks.alerts_integration.alert_foreign_logs_enricher
    .. code-block:: yaml
        customPlaybooks:
        - actions:
        - alert_foreign_logs_enricher:
            label_selectors:
            - "app={{labels.service}}"
            - "env=production"
        triggers:
          - on_prometheus_alert: {}

.. robusta-action:: playbooks.robusta_playbooks.alerts_integration.alert_definition_enricher

.. robusta-action:: playbooks.robusta_playbooks.alerts_integration.mention_enricher

Prometheus Silencers
^^^^^^^^^^^^^^^^^^^^^^^^^

These actions can selectively silence Prometheus alerts. They only work with the :ref:`on_prometheus_alert` trigger:

.. robusta-action:: playbooks.robusta_playbooks.alerts_integration.node_restart_silencer

.. robusta-action:: playbooks.robusta_playbooks.alerts_integration.severity_silencer

.. robusta-action:: playbooks.robusta_playbooks.alerts_integration.name_silencer

.. robusta-action:: playbooks.robusta_playbooks.alerts_integration.silence_alert

.. robusta-action:: playbooks.robusta_playbooks.alerts_integration.pod_status_silencer

..
    Enrichers for Specific Alerts
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    These actions enrich specific Prometheus alerts. They're very detailed and usually only relevant for one pre-defined Prometheus alert.

    .. robusta-action:: playbooks.robusta_playbooks.oom_killer.oom_killer_enricher on_prometheus_alert

    .. robusta-action:: playbooks.robusta_playbooks.cpu_throttling.cpu_throttling_analysis_enricher

    .. robusta-action:: playbooks.robusta_playbooks.daemonsets.daemonset_misscheduled_analysis_enricher

    .. robusta-action:: playbooks.robusta_playbooks.daemonsets.daemonset_misscheduled_smart_silencer
