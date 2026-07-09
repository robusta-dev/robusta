Jira Service Management
========================

Forward Jira Service Management (JSM) alerts to Robusta via the JSM outgoing webhook integration.

Prerequisites
-------------

* A Robusta account with API access.
* Your Robusta ``account_id``, found in ``generated_values.yaml``.
* A Robusta API key with ``Read/Write`` access to alerts, generated under **Settings → API Keys → New API Key**.
* Admin access to Operations in Jira Service Management.

Webhook URL
-----------

.. robusta-code::

    https://api.robusta.dev/webhooks?type=alert&origin=jsm&account_id=<ACCOUNT_ID>

Configure Jira Service Management
---------------------------------

1. In Jira Service Management, go to **Operations → Integrations → Add integration**.
2. Search for **Webhook** and select the outgoing webhook integration.
3. Set the **Webhook URL** to the URL above.
4. Add a custom **Header**:

   .. code-block::

       Authorization: Bearer <ROBUSTA_API_KEY>

5. Choose which alert actions (``Create``, ``Acknowledge``, ``Close``, …) trigger the webhook and turn the integration on.

Verify
------

Create a test alert in Jira Service Management. The event should appear in **Settings → Delivery Log** and on the Robusta timeline.
