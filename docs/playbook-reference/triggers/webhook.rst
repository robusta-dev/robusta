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

