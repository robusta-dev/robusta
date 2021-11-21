Prometheus Integration
######################

Setting up the webhook
^^^^^^^^^^^^^^^^^^^^^^
Robusta playbooks can run in response to any Prometheus alert. To configure, add the robusta-runner webhook to your alert manager configuration:

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

Trying it out
^^^^^^^^^^^^^
..
    TODO: add details here on using existing Prometheus playbooks and not just writing your own

You can now write and use a playbook action like the following:

.. admonition:: Example Prometheus playbook

    .. code-block:: python

        @action
        def my_action(alert: PrometheusKubernetesAlert):
            print(f"The alert {alert.alert_name} fired on pod {alert.pod.metadata.name}")
            print(f"The pod has these processes:", alert.pod.exec("ps aux"))
            print(f"The pod has {len(alert.pod.spec.containers)} containers")


.. tip::
    ``alert.pod`` is a Kubernetes pod object. It has the same fields as a Pod yaml. For example, ``alert.pod.metadata.name`` maps to ``metadata.name`` in the yaml.