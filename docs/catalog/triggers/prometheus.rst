.. _on_prometheus_alert:

Prometheus and AlertManager
#############################

Robusta can run actions in response to any Prometheus alert. For example:

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

Sending Alerts to Robusta
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Forward alerts to Robusta by adding a webhook receiver to AlertManager.

You can skip this step if you installed Robusta's bundled Prometheus stack.

.. admonition:: AlertManager configuration

    .. code-block:: yaml

        receivers:
          - name: 'webhook'
            webhook_configs:
              - url: 'http://robusta-runner.default.svc.cluster.local/api/alerts'
                send_resolved: true

.. warning::
    If you use the Prometheus Operator, use a `manually managed secret
    <https://github.com/prometheus-operator/prometheus-operator/blob/master/Documentation/user-guides/alerting.md#manually-managed-secret>`_
    and **not** an AlertmanagerConfig due to `this limitation <https://github.com/prometheus-operator/prometheus-operator/issues/3750>`_.

Sending Alerts to Robusta from an external Alertmanager
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

On some installations, Alertmanager may be located out of your Kubernetes cluster.

You can still send it to Robusta.

You should enable two-way interactivity to support that (```disableCloudRouting```: false, in your ```values.yaml```).

.. admonition:: External AlertManager configuration

    .. code-block:: yaml

        receivers:
          - name: 'webhook'
            webhook_configs:
              - url: 'https://api.robusta.dev/integrations/generic/alertmanager'
                http_config:
                  authorization:
                    credentials: TOKEN
                send_resolved: true

The `TOKEN` format is: `ACCOUNT_ID SIGNING_KEY`
The alerts label should contain the `cluster_name`, as defined in your `values.yaml` file

Developing actions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Here is a custom playbook action that runs on Prometheus alerts:

.. admonition:: Example Prometheus playbook

    .. code-block:: python

        @action
        def my_action(alert: PrometheusKubernetesAlert):
            print(f"The alert {alert.alert_name} fired on pod {alert.pod.metadata.name}")
            print(f"The pod has these processes:", alert.pod.exec("ps aux"))
            print(f"The pod has {len(alert.pod.spec.containers)} containers")


``alert.pod`` is a Kubernetes pod object. It will exist if the Prometheus alert had a ``pod`` label and the pod is alive
when the playbook runs. There are also ``node``, ``deployment``, and ``daemonset`` fields.
