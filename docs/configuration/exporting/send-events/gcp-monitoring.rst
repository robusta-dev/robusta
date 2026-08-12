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

.. robusta-code::

    https://api.robusta.dev/webhooks?type=alert&origin=gcp&account_id=<ACCOUNT_ID>&cluster=<CLUSTER_NAME>

Replace ``<ACCOUNT_ID>`` with your Robusta account id and ``<CLUSTER_NAME>`` with your cluster's name exactly as it appears in the Robusta UI. If ``cluster`` is omitted, alerts are filed under a generic ``external`` cluster.

Configure GCP
-------------

GCP webhook notification channels do not support custom headers in the console, so include the API key in the URL:

.. robusta-code::

    https://api.robusta.dev/webhooks?type=alert&origin=gcp&account_id=<ACCOUNT_ID>&cluster=<CLUSTER_NAME>&token=<ROBUSTA_API_KEY>

The ``token`` query parameter is accepted as an alternative to the ``Authorization`` header.

1. In the GCP Console, go to **Monitoring → Alerting → Edit Notification Channels**.
2. Click **Add new** under **Webhooks**.
3. Set the **Endpoint URL** to the URL above and name it ``Robusta``.
4. Save and attach the channel to the alerting policies you want to forward.

Verify
------

Use **Send test notification** on the channel. The event should appear in **Settings → Delivery Log** and on the Robusta timeline.
