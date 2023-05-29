Out-of-cluster Prometheus
-----------------------------------------

If AlertManager is located outside of your Kubernetes cluster then a few more steps are necessary:

1. Enable two-way interactivity in :ref:`Robusta's configuration <Configuration Overview>` by setting ``disableCloudRouting: false``
2. Make sure that your alerts contain a label named ``cluster_name`` which matches the :ref:`cluster_name defined in Robusta's configuration <Global Config>`. This is necessary so that the Robusta cloud knows which cluster to forward events to.
3. Configure AlertManager as follows:

.. admonition:: alertmanager.yaml

    .. code-block:: yaml

        receivers:
          - name: 'robusta'
            webhook_configs:
              - url: 'https://api.robusta.dev/integrations/generic/alertmanager'
                http_config:
                  authorization:
                    # Replace <TOKEN> with a string in the format `<ACCOUNT_ID> <SIGNING_KEY>`
                    credentials: <TOKEN>
                send_resolved: true

        route:
          routes:
          - receiver: 'robusta'
            matchers:
              - severity =~ "info|warn|error|critical"
            repeat_interval: 4h
            continue: true

Related Robusta Settings
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Below are additional Robusta settings related to Prometheus, AlertManager, and Grafana.

Setting up a custom Prometheus, AlertManager, and Grafana
==========================================================

If you followed the instructions on this page, Prometheus and AlertManager will know about Robusta, but Robusta might not know about them!

For certain features, Robusta needs to reach out to Prometheus and pull in extra information. This must
be configured **in addition** to updating AlertManager's configuration.

That said, most users won't need to set this up. Robusta can usually figure out where Prometheus and
other services are located. If the auto-discovery isn't working, you'll configure it manually.

Add the following to ``generated_values.yaml`` and :ref:`update Robusta <Simple Upgrade>`.


.. tab-set::

    .. tab-item:: Prometheus

        .. code-block:: yaml

          # this line should already exist
          globalConfig:
              # add the lines below
              alertmanager_url: ""
              grafana_url: ""
              prometheus_url: "http://PROMETHEUS_SERVICE_NAME.monitoring.svc.cluster.local:9090"


    .. tab-item:: VictoriaMetrics

        .. code-block:: yaml

          # this line should already exist
          globalConfig:
              # add the lines below
              alertmanager_url: ""
              grafana_url: ""
              prometheus_url: "http://VICTORIA_METRICS_SERVICE_NAME.monitoring.svc.cluster.local:8429"
