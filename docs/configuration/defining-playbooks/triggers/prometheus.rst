.. _on_prometheus_alert:

Prometheus and AlertManager
#############################

Robusta can :ref:`improve your existing Prometheus alerts <Enhanced Prometheus Alerts>`. It can also execute
:ref:`Remediation Actions <Remediate Prometheus Alerts>` in response to alerts.

Prerequisites
---------------
AlertManager must be connected to Robusta. Refer to :ref:`Sending Alerts to Robusta`.

Examples
-----------

Run a bash command on the Node associated with a specific Prometheus alert:

.. code-block:: yaml

    customPlaybooks:
    - triggers:
      - on_prometheus_alert:
          alert_name: HostHighCpuLoad
      actions:
      - node_bash_enricher:
         bash_command: ps aux

This will run the ``ps aux`` whenever a ``HostHighCpuLoad`` alert fires. The node will be chosen according to the
alert's labels. Output from the command will be sent as a :ref:`Robusta notification <Sending Notifications>`.

on_prometheus_alert
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``on_prometheus_alert`` trigger supports several filters:

.. pydantic-model:: robusta.integrations.prometheus.trigger.PrometheusAlertTrigger

Running Python Code in Response to a Alert
---------------------------------------------

If the builtin actions aren't sufficient, you can extend Robusta with your own playbook actions that respond to Prometheus alerts.

These actions are written in Python:

.. admonition:: my_playbook.py

    .. code-block:: python

        @action
        def my_action(alert: PrometheusKubernetesAlert):
            print(f"The alert {alert.alert_name} fired on pod {alert.pod.metadata.name}")
            print(f"The pod has these processes:", alert.pod.exec("ps aux"))
            print(f"The pod has {len(alert.pod.spec.containers)} containers")


``alert.pod`` is a Kubernetes pod object. It will exist if the Prometheus alert had a ``pod`` label and the pod is alive
when the playbook runs. There are also ``node``, ``deployment``, and ``daemonset`` fields.
