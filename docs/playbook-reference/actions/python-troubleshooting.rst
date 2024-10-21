Python Troubleshooting
##########################

Robusta includes built-in actions to troubleshoot, profile, and debug Python applications on Kubernetes.

These actions can be triggered automatically on Prometheus alerts, or :ref:`manually using the robusta cli <Manual Triggers>`.

.. raw:: html

  <div style="position: relative; padding-bottom: 62.5%; height: 0;"><iframe src="https://www.youtube.com/embed/N9LoJo8MgnM" frameborder="0" webkitallowfullscreen mozallowfullscreen allowfullscreen style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"></iframe></div>

.. robusta-action:: playbooks.robusta_playbooks.pod_troubleshooting.python_debugger

    This action has been deprecated. To enable it add the following to your generated_values.yaml

    .. code-block:: bash

        runner:
          additional_env_vars:
          - name: PYTHON_DEBUGGER_IMAGE
            value: debug-toolkit:v6.0

.. robusta-action:: playbooks.robusta_playbooks.pod_troubleshooting.python_profiler

    This action has been deprecated. To enable it add the following to your generated_values.yaml

    .. code-block:: bash

        runner:
          additional_env_vars:
          - name: PYTHON_DEBUGGER_IMAGE
            value: debug-toolkit:v6.0

    Manually trigger with:

    .. code-block:: bash

        robusta playbooks trigger python_profiler name=podname namespace=default process_name=your-process seconds=5

.. robusta-action:: playbooks.robusta_playbooks.pod_troubleshooting.python_memory

    This action has been deprecated. To enable it add the following to your generated_values.yaml

    .. code-block:: bash

        runner:
          additional_env_vars:
          - name: PYTHON_DEBUGGER_IMAGE
            value: debug-toolkit:v6.0

    Manually trigger with:

    .. code-block:: bash

         robusta playbooks trigger python_memory name=podname namespace=default
