Prometheus Integration
######################

Setting up the webhook
^^^^^^^^^^^^^^^^^^^^^^
Robusta playbooks can run in response to any Prometheus alert. To set this up, first add the robusta-runner webhook to your alert manager configuration:

.. code-block:: yaml

    receivers:
      - name: 'webhook'
        webhook_configs:
          - url: 'http://robusta-runner.robusta.svc.cluster.local/api/alerts'

If you use Prometheus Operator, you should instead add an AlertmanagerConfig resource with the following webhook URL

.. code-block:: python

    http://robusta-runner.robusta.svc.cluster.local/api/alerts

Trying it out
^^^^^^^^^^^^^
You can now write and use a playbook like the following:

.. code-block:: python

    @on_pod_prometheus_alert(alert_name="SomeAlert", status="firing")
    def slack_confirmation_on _cpu(alert: PrometheusPodAlert, config: HighCpuConfig):
        logging.info(f'alert fired on pod with name {alert.obj.metadata.name} in namespace {alert.obj.metadata.namespace}')

Make sure you replace "SomeAlert" with the name of your own alert.

Note that ``alert.obj`` is a Kubernetes pod object and has all fields available that a Kubernetes pod has.