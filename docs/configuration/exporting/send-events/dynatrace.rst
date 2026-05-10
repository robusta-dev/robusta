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

.. code-block::

    https://api.robusta.dev/webhooks?account_id=<ACCOUNT_ID>&origin=dynatrace&type=alert

Configure Dynatrace
-------------------

1. In Dynatrace, go to **Settings → Integration → Problem notifications** and **Set up notifications** → **Custom integration**.
2. Set the **Webhook URL** to the URL above.
3. Add a custom HTTP header:

   .. code-block::

       Authorization: Bearer <ROBUSTA_API_KEY>

4. Use the default JSON payload template, or customize it. Robusta's generic parser handles arbitrary fields.
5. Save and assign the integration to your alerting profile.

Verify
------

Use the **Send test notification** button. The event should appear in **Settings → Delivery Log** and on the Robusta timeline.
