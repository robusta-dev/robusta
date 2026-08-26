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

Run Triggered Workflows defined in the Robusta SaaS platform — typically Holmes investigations — in response to Prometheus alerts in your cluster.

.. robusta-action:: playbooks.robusta_playbooks.workflow_trigger.trigger_workflow on_prometheus_alert

    **Where to get the values:**

    * ``workflow_id`` — the id of the Triggered Workflow, copied from the workflow's page in the Robusta UI. Pass a list of ids to run several workflows from the same alert.
    * ``api_key`` — in the Robusta UI, go to **Settings → API Keys**, click **New API Key**, and grant it **Write** access to alerts. Don't commit the key to your values file — reference an environment variable instead, e.g. ``api_key: "{{ env.ROBUSTA_PLATFORM_API_KEY }}"``.

    If your Robusta account is hosted in the EU or AP region, set ``url`` to the matching regional endpoint:

    .. robusta-code:: yaml

        url: "https://api.robusta.dev/webhooks"

    For example, to run a Holmes investigation whenever a specific alert fires:

    .. code-block:: yaml

        customPlaybooks:
        - triggers:
          - on_prometheus_alert:
              alert_name: NodeCordonedManually
          actions:
          - trigger_workflow:
              workflow_id: "b7f9d2e4-1234-4c56-9abc-0123456789ab"
              api_key: "{{ env.ROBUSTA_PLATFORM_API_KEY }}"