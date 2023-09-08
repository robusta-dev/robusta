Grafana AlertManager
****************************************

If you use Grafana alerts, you're using a `special instance of AlertManager embedded inside Grafana <https://grafana.com/docs/grafana/latest/alerting/fundamentals/alertmanager/>`_.

To integrate that AlertManager with Robusta, you will need to configure both a push and a pull integration, as follows.

Configure Push Integration
============================

A push integration sends alerts from Grafana to Robusta. To configure it:

.. include:: ./_alertmanager-config.rst

.. include:: ./_pull_integration.rst

Configure Alert Silencing
==============================
For Robusta to create silences, you need to modify one additional setting. This is necessary because of minor API differences in the AlertManager embedded in Grafana.

Add the following configuration to the ``globalConfig`` section in your ``generated_values.yaml`` file:

.. admonition:: generated_values.yaml

    .. code-block:: yaml

        globalConfig: # this line should already exist
          grafana_api_key: <YOUR GRAFANA EDITOR API KEY>
          alertmanager_flavor: grafana

    .. note::

      The Grafana API key must have the ``Editor`` role in order to create silences.
