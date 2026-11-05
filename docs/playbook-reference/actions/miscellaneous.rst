Miscellaneous
########################

These actions are useful for general Kubernetes troubleshooting and everything else.

ArgoCD
^^^^^^^^^^^^^^

.. robusta-action:: playbooks.robusta_playbooks.argo_cd.argo_app_sync

Slack-OpsGenie sync
^^^^^^^^^^^^^^^^^^^^^^^^

.. robusta-action:: playbooks.robusta_playbooks.sink_enrichments.opsgenie_slack_enricher

Kubernetes Optimization
-------------------------------

.. robusta-action:: playbooks.robusta_playbooks.configuration_ab_testing.config_ab_testing

.. robusta-action:: playbooks.robusta_playbooks.disk_benchmark.disk_benchmark

Backups
-------------------

.. robusta-action:: playbooks.robusta_playbooks.pvc_snapshots.create_pvc_snapshot on_schedule

Stress Testing and Chaos Engineering
---------------------------------------------

.. robusta-action:: playbooks.robusta_playbooks.chaos_engineering.generate_high_cpu

.. robusta-action:: playbooks.robusta_playbooks.stress_tests.http_stress_test

.. robusta-action:: playbooks.robusta_playbooks.prometheus_simulation.prometheus_alert
    :manual-trigger-only:

Adding Slack user/group mentions to k8s/Prometheus events
---------------------------------------------------------
.. robusta-action:: playbooks.robusta_playbooks.alerts_integration.mention_enricher

Robusta Platform Triggered Workflows
---------------------------------------------------------

.. robusta-action:: playbooks.robusta_playbooks.workflow_trigger.trigger_workflow on_prometheus_alert

.. robusta-action:: playbooks.robusta_playbooks.workflow_trigger.trigger_workflow_event on_deployment_rollout_complete

Run a workflow after every Deployment rollout
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Pair ``trigger_workflow_event`` with :ref:`on_deployment_rollout_complete<on_deployment_rollout_complete>`
to have Holmes check each release once all its pods run the new version, with no CI/CD integration.
Add :ref:`on_deployment_rollout_failure<on_deployment_rollout_failure>` to also run it when a rollout gets stuck:

.. code-block:: yaml

    customPlaybooks:
    - name: "WorkflowOnRollout"
      triggers:
      - on_deployment_rollout_complete:
          namespace_prefix: payments
      - on_deployment_rollout_failure:
          namespace_prefix: payments
      actions:
      - trigger_workflow_event:
          workflow_id: "b7f9d2e4-1234-4c56-9abc-0123456789ab"
          api_key: "{{ env.ROBUSTA_PLATFORM_API_KEY }}"

The workflow receives a payload like the one below. ``trigger`` and the ``subject`` fields are handy for
workflow filters (e.g. ``namespace`` = ``payments``). ``description`` says whether the rollout completed or
failed, and ``resource`` is the Deployment's current manifest (Secret values are always redacted).
``rollout`` names the revision that fired: its revision number, the ReplicaSet running it and the image of
each container. On a Deployment update the controller hasn't processed yet, ``revision`` and ``replicaset``
are ``null``, because the new revision doesn't exist yet. With triggers that set ``change_filters`` (e.g. ``on_deployment_update``), the payload also
carries a ``diff`` of the fields those filters kept.

.. code-block:: json

    {
      "cluster_name": "prod-eu-1",
      "event": {
        "trigger": "DeploymentChangeEvent",
        "subject": {"kind": "deployment", "name": "checkout-api", "namespace": "payments", "node": null,
                    "labels": {"app": "checkout-api", "team": "payments"}},
        "operation": "update",
        "description": "Rollout of Deployment `checkout-api` in namespace `payments` completed",
        "rollout": {"revision": "7", "replicaset": "checkout-api-5f6b86d797",
                    "images": {"app": "registry.example.com/checkout-api:2.14.0"}},
        "resource": {"apiVersion": "apps/v1", "kind": "Deployment", "metadata": {"...": "..."},
                     "spec": {"...": "..."}, "status": {"...": "..."}}
      }
    }

The workflow's investigation looks at the cluster as it is when the run starts, not as it was when the
rollout completed. If another rollout of the same Deployment lands in between (a quick fix-forward, or a
``rollout undo`` right after a failure), the investigation sees the newer revision. Have the workflow
prompt judge the revision in ``rollout`` instead. The Deployment keeps its old ReplicaSets
(``revisionHistoryLimit``), so the ReplicaSet and its events can still be checked, though its pods are gone
once it is scaled down. For example:

.. code-block:: text

    A Deployment rollout just completed or failed; the trigger payload names it in `rollout`.
    Judge that revision: the pods of the ReplicaSet in `rollout.replicaset` running the images in
    `rollout.images`. Check that they are running and ready, and look for restarts, warning events
    and error logs. If the Deployment has since moved to another revision, say so and judge the
    revision in the payload from what remains: the ReplicaSet's status and the events of it and
    its pods. End with exactly one word, the verdict for the revision in the payload rather than the
    current one: healthy / degraded / failed, or unknown if what remains is not enough to tell.

Each cluster's runner triggers the workflow for its own rollouts, so a release rolled out to five clusters
runs the workflow five times, each against its own cluster. To run it once per release, add the playbook
only to the cluster you deploy to first. Set ``rate_limit_seconds`` to also cap how often a single
Deployment can trigger it.