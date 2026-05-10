Sentry
=======

Forward Sentry issues to Robusta via Sentry's webhook integration.

Prerequisites
-------------

* A Robusta account with API access.
* Your Robusta ``account_id``, found in ``generated_values.yaml``.
* A Robusta API key with ``Read/Write`` access to alerts.
* Sentry org-level access to install internal integrations.

Webhook URL
-----------

.. code-block::

    https://api.robusta.dev/webhooks?account_id=<ACCOUNT_ID>&origin=sentry&type=alert

Configure Sentry
----------------

Sentry's webhook destinations support custom headers via Internal Integrations:

1. In Sentry, go to **Settings → Developer Settings → New Internal Integration**.
2. Name it ``Robusta`` and grant **Issue & Event: Read** permissions.
3. Subscribe to the **issue** webhook events.
4. Set the **Webhook URL** to the URL above.
5. Add the bearer token to a **Custom Outgoing Header** named ``Authorization`` with value ``Bearer <ROBUSTA_API_KEY>`` if your Sentry plan supports it; otherwise append ``&token=<ROBUSTA_API_KEY>`` to the URL.

Verify
------

Resolve and re-open a Sentry issue, or trigger an issue alert rule that points at this integration. The event should appear in **Settings → Delivery Log** and on the Robusta timeline.
