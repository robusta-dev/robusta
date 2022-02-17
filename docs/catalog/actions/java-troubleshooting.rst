Java troubleshooting
######################

Robusta makes it easy to troubleshoot and debug Java applications running on Kubernetes.

Make sure you read about :ref:`Manual Triggers` to understand how this works.

Look at :ref:`Java Troubleshooting` for a tutorial on Java troubleshooting.

.. robusta-action:: playbooks.robusta_playbooks.java_pod_troubleshooting.java_process_inspector

.. robusta-action:: playbooks.robusta_playbooks.java_pod_troubleshooting.pod_jmap_pid

    Manually trigger with:

    .. code-block:: bash

        robusta playbooks trigger pod_jmap_pid name=podname namespace=default

.. robusta-action:: playbooks.robusta_playbooks.java_pod_troubleshooting.pod_jstack_pid

    Manually trigger with:

    .. code-block:: bash

         robusta playbooks trigger pod_jstack_pid name=podname namespace=default
