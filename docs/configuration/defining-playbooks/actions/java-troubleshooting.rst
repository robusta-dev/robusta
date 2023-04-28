Java Troubleshooting
##############################

Robusta includes built-in actions to troubleshoot and profile Java applications on Kubernetes.

These actions can be triggered automatically on Prometheus alerts, or :ref:`manually using the robusta cli <Manual Triggers>`.

For a tutorial, refer to :ref:`Java jmap and stack`.

.. robusta-action:: playbooks.robusta_playbooks.java_pod_troubleshooting.java_process_inspector

    Manually trigger with:

    .. code-block:: bash

        robusta playbooks trigger java_process_inspector name=podname namespace=default

.. robusta-action:: playbooks.robusta_playbooks.java_pod_troubleshooting.pod_jmap_pid

    Manually trigger with:

    .. code-block:: bash

        robusta playbooks trigger pod_jmap_pid name=podname namespace=default pid=pid_to_inspect

.. robusta-action:: playbooks.robusta_playbooks.java_pod_troubleshooting.pod_jstack_pid

    Manually trigger with:

    .. code-block:: bash

         robusta playbooks trigger pod_jstack_pid name=podname namespace=default pid=pid_to_inspect
