Webhooks
#########################

In-cluster webhooks
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

From inside the cluster you can trigger any manual playbook action over http:

.. code-block:: bash

    curl -X POST http://robusta-runner.default.svc.cluster.local/api/trigger \
        -H 'Content-Type: application/json' \
        -d '{"action_name": "python_debugger", "action_params": {"name": "python-debugme-58b8795b74-56fkq", "namespace": "default", "process_substring": "main"}}'

This endpoint is not exposed externally for security reasons.

External webhooks
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

From outside the cluster you can trigger manual playbook actions if you've enabled the Robusta-relay. For security reasons,
this requires the runner's signing key.

See the :ref:`Elasticsearch` integration for an example.

Prerequisites
--------------
1. The Robusta-relay must be enabled so that it can route webhooks to the appropriate Robusta runner
2. The following variables must be defined in your Helm values file:

.. code-block:: yaml

    globalConfig:
      account_id: ""       # your official Robusta account_id
      signing_key: ""      # a secret key used to verify that webhook callers are allowed to trigger playbooks
