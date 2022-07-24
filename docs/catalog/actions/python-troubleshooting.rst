Python troubleshooting
######################

Robusta makes it easy to troubleshoot and debug Python applications running on Kubernetes.

Make sure you read about :ref:`Manual Triggers` to understand how this works.

.. raw:: html

  <div style="position: relative; padding-bottom: 62.5%; height: 0;"><iframe src="https://www.youtube.com/embed/N9LoJo8MgnM" frameborder="0" webkitallowfullscreen mozallowfullscreen allowfullscreen style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"></iframe></div>

.. robusta-action:: playbooks.robusta_playbooks.pod_troubleshooting.python_debugger

.. robusta-action:: playbooks.robusta_playbooks.pod_troubleshooting.python_profiler

    Manually trigger with:

    .. code-block:: bash

        robusta playbooks trigger python_profiler name=podname namespace=default process_name=your-process seconds=5

.. robusta-action:: playbooks.robusta_playbooks.pod_troubleshooting.python_memory

    Manually trigger with:

    .. code-block:: bash

         robusta playbooks trigger python_memory name=podname namespace=default

.. robusta-action:: playbooks.robusta_playbooks.pod_troubleshooting.python_process_inspector

    Manually trigger with:

    .. code-block:: bash

         robusta playbooks trigger python_process_inspector name=podname namespace=default

.. robusta-action:: playbooks.robusta_playbooks.pod_troubleshooting.python_stack_trace

    Manually trigger with:

    .. code-block:: bash

         robusta playbooks trigger python_stack_trace name=podname namespace=default pid=process_pid
