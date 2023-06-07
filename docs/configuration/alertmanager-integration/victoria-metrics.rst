Victoria Metrics
********************

This guide walks you through configuring Victoria Metrics to push alerts to Robusta and configuring Robusta to pull additional data when needed.

Configure Push Integration
============================
To configure Victoria Metrics to send alerts to Robusta, add two settings to AlertManager:

1. A webhook receiver for Robusta
2. A route for the webhook receiver you added

.. 3. Adding :ref:`Prometheus discovery URL<Setting up a custom Prometheus, AlertManager, and Grafana>` to Robusta

Below is an example AlertManager configuration. Depending on your setup, the exact file to edit may vary. (See below.)

.. include:: ./_alertmanager-config.rst

After you configure AlertManager, you can test it works properly, by creating a demo alert:

.. code-block:: bash

    robusta demo-alert

Within a few minutes, you should see the demo alert in the Robusta UI, Slack, and any other sinks you configured.

.. admonition:: Why do I see a banner in the UI that "Alerts won't show up"?
    :class: warning

    This notification is displayed until AlertManager sends the first alert to Robusta.

Configuring a Pull Integration
====================================

.. For certain features, Robusta needs to reach out to Prometheus and pull in extra information. This must
.. be configured **in addition** to updating AlertManager's configuration.

.. That said, most users won't need to set this up. Robusta can usually figure out where Prometheus and
.. other services are located. If the auto-discovery isn't working, you'll configure it manually.

Add the following to ``generated_values.yaml`` and :ref:`update Robusta <Simple Upgrade>`.


    .. code-block:: yaml

        # this line should already exist
        globalConfig:
            # add the lines below
            alertmanager_url: ""
            grafana_url: ""
            prometheus_url: "http://VICTORIA_METRICS_SERVICE_NAME.monitoring.svc.cluster.local:8429"


.. include:: ./_additional_settings.rst