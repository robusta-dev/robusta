Grafana
#########################

This page lists Robusta actions related to Grafana.

Like all Robusta actions, these can be triggered by Prometheus/AlertManager, Kubernetes changes, :ref:`and more <Builtin triggers>`.

If you are new to Robusta, read :ref:`the tutorial <Example Playbook>` first.

Prerequisites
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
You will need a Grafana API key with write permissions.

`Generating a Grafana API key. <https://stackoverflow.com/questions/63002202/options-for-creating-a-grafana-api-token>`_

Builtin actions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. robusta-action:: playbooks.robusta_playbooks.grafana_enrichment.add_deployment_lines_to_grafana

.. robusta-action:: playbooks.robusta_playbooks.grafana_enrichment.add_alert_lines_to_grafana

.. robusta-action:: playbooks.robusta_playbooks.deployment_status_report.deployment_status_report
