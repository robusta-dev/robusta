Remediation
############################

Robusta includes actions that modify Kubernetes resources in your cluster. See also:

* :ref:`node_bash_enricher`
* :ref:`pod_bash_enricher`

.. robusta-action:: playbooks.robusta_playbooks.job_actions.alert_handling_job

.. robusta-action:: playbooks.robusta_playbooks.pod_actions.delete_pod

.. robusta-action:: playbooks.robusta_playbooks.job_actions.delete_job on_job_failure

.. robusta-action:: playbooks.robusta_playbooks.autoscaler.alert_on_hpa_reached_limit on_horizontalpodautoscaler_update

.. robusta-action:: playbooks.robusta_playbooks.workload_actions.rollout_restart on_prometheus_alert

.. robusta-action:: playbooks.robusta_playbooks.workload_actions.restart_named_rollout on_prometheus_alert

Node
*****************

.. robusta-action:: playbooks.robusta_playbooks.node_actions.cordon on_node_create

.. robusta-action:: playbooks.robusta_playbooks.node_actions.uncordon on_node_create

.. robusta-action:: playbooks.robusta_playbooks.node_actions.drain on_node_create
