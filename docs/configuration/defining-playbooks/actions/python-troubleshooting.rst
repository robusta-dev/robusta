Python Troubleshooting
##########################

Robusta includes built-in actions to troubleshoot, profile, and debug Python applications on Kubernetes.

These actions can be triggered automatically on Prometheus alerts, or :ref:`manually using the robusta cli <Manual Triggers>`.

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
