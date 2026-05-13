Opsgenie
=========

Forward Opsgenie alerts to Robusta via the Opsgenie outgoing webhook integration.

Prerequisites
-------------

* A Robusta account with API access.
* Your Robusta ``account_id``, found in ``generated_values.yaml``.
* A Robusta API key with ``Read/Write`` access to alerts.
* Opsgenie admin access.

Webhook URL
-----------

.. code-block::

    https://api.robusta.dev/webhooks?type=alert&origin=opsgenie&account_id=<ACCOUNT_ID>

Configure Opsgenie
------------------

1. In Opsgenie, go to **Settings → Integrations → Add Integration → Webhook**.
2. Set the **Webhook URL** to the URL above.
3. Add a custom **Header**:

   .. code-block::

       Authorization: Bearer <ROBUSTA_API_KEY>

4. Choose which alert actions (``Create``, ``Acknowledge``, ``Close``, …) trigger the webhook and save.

Verify
------

Create a test alert in Opsgenie. The alert should appear on the Robusta timeline.
