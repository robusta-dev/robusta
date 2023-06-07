In-cluster Prometheus
****************************************

This guide walks you through configuring your in-cluster Prometheus to push alerts to Robusta and also configuring Robusta to pull additional data when needed.

Configure Push Integration
============================
To configure Prometheus to send alerts to Robusta, add two settings to AlertManager:

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

.. include:: ./_pull_integration.rst

.. include:: ./_additional_settings.rst