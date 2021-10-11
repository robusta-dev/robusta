Prometheus Integration
######################

Setting up the webhook
^^^^^^^^^^^^^^^^^^^^^^
Robusta playbooks can run in response to any Prometheus alert. To set this up, first add the robusta-runner webhook to your alert manager configuration:

.. code-block:: yaml

    receivers:
      - name: 'webhook'
        webhook_configs:
          - url: 'http://robusta-runner.default.svc.cluster.local/api/alerts'
            send_resolved: true

If you use Prometheus Operator, configure AlertManager using a `manually managed secret <https://github.com/prometheus-operator/prometheus-operator/blob/master/Documentation/user-guides/alerting.md#manually-managed-secret>`_ and **not** an AlertmanagerConfig.
`Otherwise you can only monitor alerts in the same namespace as the AlertManagerConfig <https://github.com/prometheus-operator/prometheus-operator/issues/3750>`_ for details.

.. code-block:: python

    http://robusta-runner.default.svc.cluster.local/api/alerts

Trying it out
^^^^^^^^^^^^^
You can now write and use a playbook like the following:

.. code-block:: python

    @on_pod_prometheus_alert(alert_name="SomeAlert", status="firing")
    def slack_confirmation_on _cpu(alert: PrometheusPodAlert, config: HighCpuConfig):
        logging.info(f'alert fired on pod with name {alert.obj.metadata.name} in namespace {alert.obj.metadata.namespace}')

Make sure you replace "SomeAlert" with the name of your own alert.

.. tip::
    ``alert.obj`` is a Kubernetes pod object. It has the same fields as a pod's yaml. For example, ``alert.obj.metadata.name`` maps to ``metadata.name`` in the yaml.