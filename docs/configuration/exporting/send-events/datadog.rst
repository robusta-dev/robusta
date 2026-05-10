Datadog
========

Forward Datadog monitor alerts to Robusta via a Datadog webhook integration.

Prerequisites
-------------

* A Robusta account with API access.
* Your Robusta ``account_id``, found in ``generated_values.yaml``.
* A Robusta API key with ``Read/Write`` access to alerts.
* A Datadog admin able to create webhook integrations.

Webhook URL
-----------

.. code-block::

    https://api.robusta.dev/webhooks?account_id=<ACCOUNT_ID>&origin=datadog&type=alert

Configure Datadog
-----------------

1. In Datadog, go to **Integrations → Webhooks → New** and name the webhook ``robusta``.
2. Set the URL to the webhook URL above.
3. Under **Custom Headers**, add:

   .. code-block:: json

       { "Authorization": "Bearer <ROBUSTA_API_KEY>" }

4. Leave the default payload, or customize it. Robusta's per-origin parser handles the standard Datadog payload shape.
5. Save. In any monitor, set the **Notify** field to ``@webhook-robusta`` to forward its alerts to Robusta.

Verify
------

Trigger a test alert from a Datadog monitor. The event should appear in **Settings → Delivery Log** and on the Robusta timeline.
