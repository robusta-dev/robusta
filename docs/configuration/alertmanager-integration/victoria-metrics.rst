Victoria Metrics
********************

This guide walks you through configuring `Victoria Metrics <https://victoriametrics.com/>`_ with Robusta.

You will need to configure two integrations: both a push integration and a pull integration.

Configure Push Integration
============================

A push integration sends alerts to Robusta. To configure it, edit AlertManager's configuration:

.. include:: ./_alertmanager-config.rst

.. include:: ./_testing_integration.rst

Configure Pull Integration
====================================

A pull integration lets Robusta pull metrics and create silences.

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

.. code-annotations::
    1. This is necessary for Robusta to create silences when using Grafana Alerts, because of minor API differences in the AlertManager embedded in Grafana.

Optional Settings
==================

**Prometheus flags checks**

.. include:: ./_prometheus_flags_check.rst
