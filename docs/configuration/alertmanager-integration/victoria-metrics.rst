Victoria Metrics
********************

This guide walks you through configuring Victoria Metrics to push alerts to Robusta and configuring Robusta to pull additional data when needed.

Configure Push Integration
============================
To configure Victoria Metrics to send alerts to Robusta, add two settings to AlertManager:

1. A Robusta webhook receiver.
2. A route for the newly added webhook receiver.

Below is an example AlertManager configuration.

.. include:: ./_alertmanager-config.rst

.. include:: ./_testing_integration.rst

Configuring a Pull Integration
====================================

Add the following to ``generated_values.yaml`` and :ref:`update Robusta <Simple Upgrade>`.


    .. code-block:: yaml

        # this line should already exist
        globalConfig:
            # add the lines below
            alertmanager_url: "http://ALERT_MANAGER_SERVICE_NAME.NAMESPACE.svc.cluster.local:9093"
            grafana_url: ""
            prometheus_url: "http://VICTORIA_METRICS_SERVICE_NAME.NAMESPACE.svc.cluster.local:8429"
             # Additional query string parameters to be appended to the Prometheus connection URL (optional)
            prometheus_url_query_string: "demo-query=example-data&another-query=value"


.. include:: ./_additional_settings.rst
