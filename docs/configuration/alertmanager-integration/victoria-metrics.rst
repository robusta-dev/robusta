Victoria Metrics
********************

This guide walks you through configuring `Victoria Metrics <https://victoriametrics.com/>`_ with Robusta.

You will need to configure two integrations: one to send alerts to Robusta and another to let Robusta query metrics and create silences.

Send Alerts to Robusta
============================

To configure, edit AlertManager's configuration:

.. include:: ./_alertmanager-config.rst

.. include:: ./_testing_integration.rst

Configure Metric Querying
====================================

Metrics querying lets Robusta pull metrics and create silences.

Add the following to ``generated_values.yaml`` and :ref:`update Robusta <Simple Upgrade>`.

.. code-block:: yaml

    globalConfig: # this line should already exist
        # add the lines below
        alertmanager_url: "http://ALERT_MANAGER_SERVICE_NAME.NAMESPACE.svc.cluster.local:9093"
        grafana_url: ""
        prometheus_url: "http://VICTORIA_METRICS_SERVICE_NAME.NAMESPACE.svc.cluster.local:8429"
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
==================

**Prometheus flags checks**

.. include:: ./_prometheus_flags_check.rst
