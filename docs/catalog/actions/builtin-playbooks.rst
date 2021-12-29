List of built-in playbooks
############################

Application Visibility and Troubleshooting
-------------------------------------------

.. robusta-action:: playbooks.robusta_playbooks.restart_loop_reporter.restart_loop_reporter

.. robusta-action:: playbooks.robusta_playbooks.pod_troubleshooting.pod_ps

Kubernetes Error Handling
-------------------------

.. robusta-action:: playbooks.robusta_playbooks.node_enrichments.node_health_watcher

.. robusta-action:: playbooks.robusta_playbooks.autoscaler.alert_on_hpa_reached_limit

.. robusta-action:: playbooks.robusta_playbooks.autoscaler.scale_hpa_callback

Kubernetes Monitoring
---------------------

.. robusta-action:: playbooks.robusta_playbooks.git_change_audit.git_change_audit

.. robusta-action:: playbooks.robusta_playbooks.deployment_status_report.deployment_status_report

.. robusta-action:: playbooks.robusta_playbooks.babysitter.resource_babysitter

.. robusta-action:: playbooks.robusta_playbooks.networking.incluster_ping

Integrations
-------------------------------------------

.. robusta-action:: playbooks.robusta_playbooks.argo_cd.argo_app_sync

Kubernetes Optimization
-----------------------

.. robusta-action:: playbooks.robusta_playbooks.configuration_ab_testing.config_ab_testing

.. robusta-action:: playbooks.robusta_playbooks.disk_benchmark.disk_benchmark

Stress Testing and Chaos Engineering
------------------------------------

.. robusta-action:: playbooks.robusta_playbooks.chaos_engineering.generate_high_cpu

.. robusta-action:: playbooks.robusta_playbooks.stress_tests.http_stress_test

.. robusta-action:: playbooks.robusta_playbooks.prometheus_simulation.prometheus_alert

Alert Enrichment
---------------------
This is a special playbook that has out-of-the box knowledge about specific Prometheus alerts. See :ref:`prometheus-alert-enrichment` for details.