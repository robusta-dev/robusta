Victoria Metrics
********************

This guide walks you through configuring `Victoria Metrics <https://victoriametrics.com/>`_ with Robusta.

You will need to configure two integrations: one to send alerts to Robusta and another to let Robusta query metrics and create silences.

Send Alerts to Robusta
============================

Add the following to your Victoria Metrics Alertmanager configuration (e.g., Helm values file or VMAlertmanagerConfig CRD):

.. code-block:: yaml

    receivers:
      - name: 'robusta'
      webhook_configs:
          - url: 'http://<ROBUSTA-HELM-RELEASE-NAME>-runner.<NAMESPACE>.svc.cluster.local/api/alerts'
          send_resolved: true # (3)

    route: # (1)
      routes:
      - receiver: 'robusta'
          group_by: [ '...' ]
          group_wait: 1s
          group_interval: 1s
          matchers:
          - severity =~ ".*"
          repeat_interval: 4h
          continue: true # (2)

.. code-annotations::
    1. Put Robusta's route as the first route, to guarantee it receives alerts. If you can't do so, you must guarantee all previous routes has ``continue: true`` set.
    2. Keep sending alerts to receivers defined after Robusta.
    3. Important, so Robusta knows when alerts are resolved.


.. include:: ./_testing_integration.rst

Configure Metrics Querying
====================================

Robusta can query metrics and create silences using Victoria Metrics. If both are in the same Kubernetes cluster, Robusta can auto-detect the Victoria Metrics service. To verify, go to the "Apps" tab in Robusta, select an application, and check for usage graphs.

If auto-detection fails you must add the ``prometheus_url`` parameter and :ref:`update Robusta <Simple Upgrade>`.

.. code-block:: yaml

    globalConfig: # this line should already exist
        # add the lines below
        alertmanager_url: "http://<VM_ALERT_MANAGER_SERVICE_NAME>.<NAMESPACE>.svc.cluster.local:9093" # Example:"http://vmalertmanager-victoria-metrics-vm.default.svc.cluster.local:9093/"        
        prometheus_url: "http://VM_Metrics_SERVICE_NAME.NAMESPACE.svc.cluster.local:8429" # Example:"http://vmsingle-vmks-victoria-metrics-k8s-stack.default.svc.cluster.local:8429"
        # Add any labels that are relevant to the specific cluster (optional)
        # prometheus_additional_labels:
        #   cluster: 'CLUSTER_NAME_HERE'

        # Additional query string parameters to be appended to the Prometheus connection URL (optional)
        # prometheus_url_query_string: "demo-query=example-data&another-query=value"

        # Create alert silencing when using Grafana alerts (optional)
        # grafana_api_key: <YOUR GRAFANA EDITOR API KEY> # (1)
        # alertmanager_flavor: grafana

.. code-annotations::
    1. This is necessary for Robusta to create silences when using Grafana Alerts, because of minor API differences in the AlertManager embedded in Grafana.

Optional Settings
==================

**Prometheus flags checks**

.. include:: ./_prometheus_flags_check.rst
