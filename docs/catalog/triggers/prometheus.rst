Prometheus and AlertManager
#############################

Robusta can run actions in response to any Prometheus alert. This is configured via AlertManager webhooks.

When an alert has a ``pod`` label then the Pod will be automatically loaded and passed to the Robusta action. This applies
to many Kubernetes resources like Pod, Deployment, Job, and DaemonSet.

Example
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: yaml

    customPlaybooks:
    - triggers:
      - on_prometheus_alert:
          alert_name: HostHighCpuLoad
      actions:
      - node_cpu_enricher: {}
      - graph_enricher: {}

Supported filters
^^^^^^^^^^^^^^^^^^^^^^

.. pydantic-model:: robusta.integrations.prometheus.trigger.PrometheusAlertTrigger

Sending Alerts to Robusta
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Forward alerts to Robusta by adding a webhook receiver to AlertManager:

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
