Miscellaneous
########################

These actions are useful for general Kubernetes troubleshooting and everything else.

ArgoCD
^^^^^^^^^^^^^^

.. robusta-action:: playbooks.robusta_playbooks.argo_cd.argo_app_sync

Kubernetes Optimization
-----------------------

.. robusta-action:: playbooks.robusta_playbooks.configuration_ab_testing.config_ab_testing

.. robusta-action:: playbooks.robusta_playbooks.disk_benchmark.disk_benchmark

Backups
-------------------

.. robusta-action:: playbooks.robusta_playbooks.pvc_snapshots.create_pvc_snapshot
    :recommended-trigger: on_schedule

Stress Testing and Chaos Engineering
------------------------------------

.. robusta-action:: playbooks.robusta_playbooks.chaos_engineering.generate_high_cpu

.. robusta-action:: playbooks.robusta_playbooks.stress_tests.http_stress_test

.. robusta-action:: playbooks.robusta_playbooks.prometheus_simulation.prometheus_alert
    :manual-trigger-only:

Adding Slack user/group mentions to k8s/Prometheus events
---------------------------------------------------------
.. robusta-action:: playbooks.robusta_playbooks.alerts_integration.mention_enricher
