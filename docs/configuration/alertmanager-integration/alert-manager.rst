In-cluster Prometheus
****************************************

This guide walks you through integrating an in-cluster Prometheus with Robusta. You will need to configure two integrations: both a push integration and a pull integration.

Configure Push Integration
============================
A push integrations is required for AlertManager to push alerts to Robusta. To configure it, you must add a receiver and route to AlertManger's configuration:

.. include:: ./_alertmanager-config.rst

To test this, we can send a dummy alert to AlertManager:

.. code-block:: bash

    robusta demo-alert

If everything was configured properly, AlertManager will push this alert to Robusta. The alert will show up in the Robusta UI, Slack, and any other configured sinks.

.. admonition:: I configured AlertManager, but I'm still not receiving alerts?
    :class: warning

    Try sending a demo-alert as described above, and check the AlertManager logs for errors. Or reach out to us on `Slack <https://bit.ly/robusta-slack>`_.

.. include:: ./_pull_integration.rst

.. include:: ./_additional_settings.rst
