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
            alertmanager_url: ""
            grafana_url: ""
            prometheus_url: "http://VICTORIA_METRICS_SERVICE_NAME.monitoring.svc.cluster.local:8429"


.. include:: ./_additional_settings.rst
