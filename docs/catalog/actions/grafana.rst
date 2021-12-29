Grafana
#########################

Robusta playbooks can:

1. Write annotations to Grafana
2. Fetch graphs from Grafana and send them to Slack

Prerequisites
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
You will need a Grafana API key with write permissions.

`Generating a Grafana API key. <https://stackoverflow.com/questions/63002202/options-for-creating-a-grafana-api-token>`_

Builtin actions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. robusta-action:: playbooks.robusta_playbooks.grafana_enrichment.add_deployment_lines_to_grafana

.. robusta-action:: playbooks.robusta_playbooks.grafana_enrichment.add_alert_lines_to_grafana

.. robusta-action:: playbooks.robusta_playbooks.deployment_status_report.deployment_status_report
