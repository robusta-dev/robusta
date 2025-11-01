Grafana Cloud
*************

This guide shows how to send alerts from Grafana Cloud's AlertManager to Robusta.

For configuring metric querying and advanced settings, see :doc:`/configuration/metric-providers-grafana-cloud`.

Send Alerts to Robusta
=======================

Configure Grafana Cloud to forward alerts to Robusta:

1. **Get Your Webhook URL**:

   - Log into the Robusta UI
   - Navigate to ``Settings`` > ``Advanced``
   - In the Grafana webhook section, click ``Generate URL``
   - Save the generated webhook URL

2. **Create Contact Point in Grafana Cloud**:

   - Log into your Grafana Cloud instance
   - Go to ``Alerting`` > ``Contact points``
   - Click ``Add contact point``
   - Set **Name**: ``robusta``
   - Set **Integration**: ``Webhook``
   - Set **URL**: Paste the webhook URL from step 1
   - Click ``Test`` to verify connectivity
   - Click ``Save contact point``

3. **Configure Notification Policy**:

   - Go to ``Alerting`` > ``Notification policies``
   - Edit the default policy or create a new one
   - Set the contact point to ``robusta``
   - Save the policy

.. details:: Why do I see a banner in the UI that "Alerts won't show up"?
    :class: warning

    This notification is displayed until the first alert arrives at Robusta.

Configure Metric Querying
==========================

To enable Robusta to pull metrics from Grafana Cloud's Mimir, see :doc:`/configuration/metric-providers-grafana-cloud`.
