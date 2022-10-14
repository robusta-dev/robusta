.. _on_prometheus_alert:

Prometheus and AlertManager
#############################

The first step is to configure AlertManager to send alerts to Robusta. see :ref:`Sending Alerts to Robusta`

Robusta can run actions in response to any Prometheus alert.
For example:

.. code-block:: yaml

    customPlaybooks:
    - triggers:
      - on_prometheus_alert:
          alert_name: HostHighCpuLoad
      actions:
      - node_bash_enricher:
         bash_command: ps aux

This will run the ``ps aux`` on the relevant node whenever a ``HostHighCpuLoad`` alert fires. The output will be
sent to the default sinks.

How it works
^^^^^^^^^^^^^^^^^

Relevant Kubernetes resources are loaded from the alert's metadata. Then Robusta actions are run with those resources
as input.

In the example above, the ``node_cpu_enricher`` receives the node on which the alert fired.

Limiting when on_prometheus_alert fires
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can limit when the automation runs by applying the following filters to ``on_prometheus_alert``:

.. pydantic-model:: robusta.integrations.prometheus.trigger.PrometheusAlertTrigger

Developing actions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Here is a custom playbook action that runs on Prometheus alerts:

.. admonition:: my_playbook.py

    .. code-block:: python

        @action
        def my_action(alert: PrometheusKubernetesAlert):
            print(f"The alert {alert.alert_name} fired on pod {alert.pod.metadata.name}")
            print(f"The pod has these processes:", alert.pod.exec("ps aux"))
            print(f"The pod has {len(alert.pod.spec.containers)} containers")


``alert.pod`` is a Kubernetes pod object. It will exist if the Prometheus alert had a ``pod`` label and the pod is alive
when the playbook runs. There are also ``node``, ``deployment``, and ``daemonset`` fields.
