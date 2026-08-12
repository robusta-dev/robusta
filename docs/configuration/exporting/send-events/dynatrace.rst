Dynatrace
==========

Forward Dynatrace problems to Robusta via a Dynatrace custom webhook integration.

Prerequisites
-------------

* A Robusta account with API access.
* Your Robusta ``account_id``, found in ``generated_values.yaml``.
* A Robusta API key with ``Read/Write`` access to alerts.
* A Dynatrace admin able to add problem notifications.

Webhook URL
-----------

.. robusta-code::

    https://api.robusta.dev/webhooks?type=alert&origin=dynatrace&account_id=<ACCOUNT_ID>&cluster=<CLUSTER_NAME>

Replace ``<ACCOUNT_ID>`` with your Robusta account id, and ``<CLUSTER_NAME>`` with the name of the cluster to file alerts under. The name must exactly match the cluster's name as it appears in the Robusta UI (the ``clusterName`` your Robusta agent was installed with). If ``cluster`` is omitted, alerts are silently filed under a generic ``external`` cluster.

Configure Dynatrace
-------------------

1. In Dynatrace, go to **Settings → Integration → Problem notifications** and **Set up notifications** → **Custom integration**.
2. Set the **Webhook URL** to the URL above.
3. Add a custom HTTP header:

   .. code-block::

       Authorization: Bearer <ROBUSTA_API_KEY>

4. Use the default JSON payload template.
5. Save and assign the integration to your alerting profile.

Verify
------

Use the **Send test notification** button. The event should appear in **Settings → Delivery Log** and on the Robusta timeline.
