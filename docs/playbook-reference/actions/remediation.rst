Remediation
############################

Robusta includes actions that modify Kubernetes resources in your cluster. Most of them need a
``runner.rbac`` flag, see :ref:`read-only-service-account`.

.. warning::

    ``alert_handling_job`` is deprecated and no longer supported. It logs an error and returns an error without creating a Job.

.. robusta-action:: playbooks.robusta_playbooks.job_actions.alert_handling_job

.. robusta-action:: playbooks.robusta_playbooks.pod_actions.delete_pod

.. robusta-action:: playbooks.robusta_playbooks.pod_actions.delete_alert_pod on_prometheus_alert

.. robusta-action:: playbooks.robusta_playbooks.job_actions.delete_job on_job_failure

.. robusta-action:: playbooks.robusta_playbooks.autoscaler.alert_on_hpa_reached_limit on_horizontalpodautoscaler_update

.. warning::

    ``rollout_restart`` is deprecated and no longer supported. It logs an error and returns an error without restarting the workload.

.. robusta-action:: playbooks.robusta_playbooks.workload_actions.rollout_restart

Node
*****************

.. robusta-action:: playbooks.robusta_playbooks.node_actions.cordon on_node_create

.. robusta-action:: playbooks.robusta_playbooks.node_actions.uncordon on_node_create

.. robusta-action:: playbooks.robusta_playbooks.node_actions.drain on_node_create

Kubectl
*****************

.. warning::

    ``kubectl_command`` is deprecated and no longer supported. It logs an error and returns an error without running the command.

.. robusta-action:: playbooks.robusta_playbooks.kubectl_enrichments.kubectl_command
