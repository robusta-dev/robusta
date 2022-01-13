Python troubleshooting
######################

Robusta makes it easy to troubleshoot and debug Python applications running on Kubernetes.

Make sure you read about :ref:`Manual Triggers` to understand how this works.

.. robusta-action:: playbooks.robusta_playbooks.pod_troubleshooting.python_debugger

.. robusta-action:: playbooks.robusta_playbooks.pod_troubleshooting.python_profiler

    Manually trigger with:

    .. code-block:: bash

        robusta playbooks trigger python_profiler pod_name=your-pod namespace=you-ns process_name=your-process seconds=5

.. robusta-action:: playbooks.robusta_playbooks.pod_troubleshooting.python_memory

    Manually trigger with:

    .. code-block:: bash

         robusta playbooks trigger python_memory name=myapp namespace=default process_substring=main