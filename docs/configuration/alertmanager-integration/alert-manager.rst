In-cluster Prometheus
****************************************

This guide walks you through integrating an in-cluster Prometheus with Robusta. You will need to configure two integrations: both a push integration and a pull integration.

Configure Push Integration
============================
A push integrations is required for AlertManager to push alerts to Robusta. To configure it, you must add a receiver and route to AlertManger's configuration:

.. include:: ./_alertmanager-config.rst

.. include:: ./_testing_integration.rst

.. include:: ./_pull_integration.rst

.. include:: ./_additional_settings.rst
