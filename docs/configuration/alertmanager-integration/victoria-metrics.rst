Victoria Metrics
********************

This guide walks you through configuring `Victoria Metrics <https://victoriametrics.com/>`_ with Robusta. You will need to configure two integrations: both a push integration and a pull integration.

Configure Push Integration
============================
A push integration is required for AlertManager to push alerts to Robusta. To configure it, you must add a receiver and route to AlertManager's configuration.

Copy the configuration below to the appropriate AlertManager config file:

.. include:: ./_alertmanager-config.rst

.. include:: ./_testing_integration.rst

Configuring a Pull Integration
====================================

Add the following to ``generated_values.yaml`` and :ref:`update Robusta <Simple Upgrade>`.


.. code-block:: yaml

    globalConfig: # this line should already exist
        # add the lines below
        alertmanager_url: "http://ALERT_MANAGER_SERVICE_NAME.NAMESPACE.svc.cluster.local:9093"
        grafana_url: ""
        prometheus_url: "http://VICTORIA_METRICS_SERVICE_NAME.NAMESPACE.svc.cluster.local:8429"
            # Additional query string parameters to be appended to the Prometheus connection URL (optional)
        prometheus_url_query_string: "demo-query=example-data&another-query=value"


.. include:: ./_additional_settings.rst
