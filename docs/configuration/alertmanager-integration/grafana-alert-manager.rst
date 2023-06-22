Grafana AlertManager
****************************************

This guide walks you through integrating a `Grafana AlertManager <https://grafana.com/docs/grafana/latest/alerting/fundamentals/alertmanager/>`_ with Robusta. You will need to configure two integrations: both a push integration and a pull integration.

Configure Push Integration
============================
A push integrations is required for AlertManager to push alerts to Robusta. To configure it, you must add a receiver and route to AlertManger's configuration:

.. include:: ./_alertmanager-config.rst

.. include:: ./_testing_integration.rst

.. include:: ./_pull_integration.rst

Configure Alert Silencing
=====================
For Robusta to create silences, you need to modify one additional setting. This is necessary because of minor API differences in the AlertManager embedded in Grafana.

Add the following configuration to the ``globalConfig`` section in your ``generated_values.yaml`` file:

.. admonition:: generated_values.yaml

    .. code-block:: yaml

        globalConfig:
          grafana_api_key: <YOUR GRAFANA EDITOR API KEY>
          alertmanager_flavor: grafana

    .. note::

      The Grafana API key must have the ``Editor`` role in order to create silences.

.. include:: ./_additional_settings.rst
