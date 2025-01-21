Disable "OOMKill" Notifications
===================================

Configure Robusta to not send OOMKill notifications by disabling the built-in OOMKill playbook. 

.. code-block:: yaml

    disabledPlaybooks:
    - PodOOMKill

However you can still create your custom OOMKill notification using the ``kube_pod_container_status_last_terminated_reason{reason="OOMKilled"}`` Prometheus metric.