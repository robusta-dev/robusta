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

Kubectl
*****************

.. robusta-action:: playbooks.robusta_playbooks.kubectl_enrichments.kubectl_command

    Use `kubectl_command` to run kubectl with dynamic placeholders:
    - `$namespace`: resource namespace
    - `$kind`: resource kind (e.g., Pod, Deployment)
    - `$name`: resource name

    Example: **Scale Down Deployment on Crash Loop**

    .. code-block:: yaml

        customPlaybooks:
        - name: CrashLoopScaleDown
          triggers:
          - on_pod_crash_loop:
              restart_count: 3
          actions:
            - kubectl_command:
                description: "Scale Down Deployment"
                command: kubectl scale --replicas=0 deployment/payment-processing-worker -n $namespace

    If the pod is in the `production` namespace, the command will be:

    .. code-block:: bash

        kubectl scale --replicas=0 deployment/payment-processing-worker -n production

    Example: **Delete Crashing Resource**

    This deletes the crashing resource by kind, name, and namespace:

    .. code-block:: bash

        kubectl delete $kind $name -n $namespace

    For example, deleting a crashing pod named `api-worker-1` in the `staging` namespace:

    .. code-block:: bash

        kubectl delete Pod api-worker-1 -n staging
