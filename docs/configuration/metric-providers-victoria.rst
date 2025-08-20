VictoriaMetrics
===============

Configure Robusta to use VictoriaMetrics as your metrics provider.

Quick Start
--------------

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

        # If using a multi-tenant prometheus or alertmanager, pass the org id to all queries
        # prometheus_additional_headers:
        #   X-Scope-OrgID: <org id>
        # alertmanager_additional_headers:
        #   X-Scope-OrgID: <org id>

.. code-annotations::
    1. This is necessary for Robusta to create silences when using Grafana Alerts, because of minor API differences in the AlertManager embedded in Grafana.

Optional Settings
----------------------

**Prometheus flags checks**

Robusta utilizes the flags API to retrieve data from Prometheus-style metric stores. However, some platforms like Google Managed Prometheus, Azure Managed Prometheus etc, do not implement the flags API.

You can disable the Prometheus flags API check by setting the following option to false.

.. code-block:: yaml

    globalConfig:
      check_prometheus_flags: true/false

Next Steps
----------

- Configure :doc:`alert routing </notification-routing/index>`
- Set up :doc:`VictoriaMetrics alerts </configuration/alertmanager-integration/victoria-metrics>`
- Learn about :doc:`common configuration options <metric-providers>`