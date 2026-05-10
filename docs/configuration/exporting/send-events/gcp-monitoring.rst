GCP Cloud Monitoring
=====================

Forward Cloud Monitoring alerting policies to Robusta via a GCP webhook notification channel.

Prerequisites
-------------

* A Robusta account with API access.
* Your Robusta ``account_id``, found in ``generated_values.yaml``.
* A Robusta API key with ``Read/Write`` access to alerts.
* A GCP project with the ``Monitoring Notification Channel Editor`` role.

Webhook URL
-----------

.. code-block::

    https://api.robusta.dev/webhooks?account_id=<ACCOUNT_ID>&origin=gcp&type=alert

Configure GCP
-------------

GCP webhook notification channels do not support custom headers in the console, so include the API key in the URL:

.. code-block::

    https://api.robusta.dev/webhooks?account_id=<ACCOUNT_ID>&origin=gcp&type=alert&token=<ROBUSTA_API_KEY>

The relay accepts ``token`` as an alternate to the ``Authorization`` header.

1. In the GCP Console, go to **Monitoring → Alerting → Edit Notification Channels**.
2. Click **Add new** under **Webhooks**.
3. Set the **Endpoint URL** to the URL above and name it ``Robusta``.
4. Save and attach the channel to the alerting policies you want to forward.

Verify
------

Use **Send test notification** on the channel. The event should appear in **Settings → Delivery Log** and on the Robusta timeline.
