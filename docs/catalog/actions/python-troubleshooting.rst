Python troubleshooting
######################

Robusta makes it easy to troubleshoot and debug Python applications running on Kubernetes.

Make sure you read about :ref:`Manual Triggers` to understand how this works.

.. raw:: html

  <div style="position: relative; padding-bottom: 62.5%; height: 0;"><iframe src="https://www.loom.com/embed/5d18fa1283fa4d80b71f7d415d2cbe66" frameborder="0" webkitallowfullscreen mozallowfullscreen allowfullscreen style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"></iframe></div>

.. robusta-action:: playbooks.robusta_playbooks.pod_troubleshooting.python_debugger

.. robusta-action:: playbooks.robusta_playbooks.pod_troubleshooting.python_profiler

    Manually trigger with:

    .. code-block:: bash

        robusta playbooks trigger python_profiler pod_name=your-pod namespace=you-ns process_name=your-process seconds=5

.. robusta-action:: playbooks.robusta_playbooks.pod_troubleshooting.python_memory

    Manually trigger with:

    .. code-block:: bash

         robusta playbooks trigger python_memory name=myapp namespace=default process_substring=main