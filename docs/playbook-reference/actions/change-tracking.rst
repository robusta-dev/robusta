Change Tracking
############################

These actions were built for tracking changes in your cluster

.. robusta-action:: playbooks.robusta_playbooks.git_change_audit.git_change_audit
    :recommended-trigger: on_kubernetes_any_resource_all_changes

.. robusta-action:: playbooks.robusta_playbooks.deployment_status_report.deployment_status_report
    :recommended-trigger: on_deployment_update

.. robusta-action:: playbooks.robusta_playbooks.grafana_enrichment.add_deployment_lines_to_grafana
    :recommended-trigger: on_deployment_update
    :reference-label: change_tracking__add_deployment_lines_to_grafana

.. robusta-action:: playbooks.robusta_playbooks.babysitter.resource_babysitter
    :recommended-trigger: on_deployment_update
