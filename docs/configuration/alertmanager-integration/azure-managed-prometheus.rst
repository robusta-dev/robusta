Azure Managed Prometheus Alerts
*********************************

This guide shows how to send alerts from Azure Managed Prometheus to Robusta.

For configuring metric querying and advanced settings, see :doc:`/configuration/metric-providers-azure`.

Send Alerts to Robusta
===============================

This integration sends Azure Managed Prometheus alerts to Robusta. To configure it:

1. Login to the Robusta UI and navigate to the ``Settings`` > ``Advanced`` tab.
2. In the Azure Webhook section click ``Generate URL`` and save the generated url.
3. Login to the Microsoft Azure Portal, go to ``Alerts`` > ``Action groups``
4. Create a new action group, or edit an existing one.
5. Under the `Actions` tabs (**not** the Notifications tab) add a ``Webhook`` and copy the url from step 2, into the URI input. Make sure to select ``Enable the common alert schema``.

.. details:: Why do I see a banner in the UI that "Alerts won't show up"?
    :class: warning

    This notification is displayed until the first alert to Robusta.

Configure Metric Querying
===============================

To enable Robusta to pull metrics from Azure Managed Prometheus, see :doc:`/configuration/metric-providers-azure`.
