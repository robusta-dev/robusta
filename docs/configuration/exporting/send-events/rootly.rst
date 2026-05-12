Rootly
=======

Forward Rootly incidents to Robusta via a Rootly outgoing webhook.

Prerequisites
-------------

* A Robusta account with API access.
* Your Robusta ``account_id``, found in ``generated_values.yaml``.
* A Robusta API key with ``Read/Write`` access to alerts.
* Rootly admin access.

Webhook URL
-----------

.. code-block::

    https://api.robusta.dev/webhooks?type=incident&origin=rootly&account_id=<ACCOUNT_ID>

Configure Rootly
----------------

1. In Rootly, go to **Integrations → Outgoing Webhooks → New webhook**.
2. Set the **URL** to the URL above and name it ``Robusta``.
3. Add a custom header:

   .. code-block::

       Authorization: Bearer <ROBUSTA_API_KEY>

4. Subscribe to the incident events you want forwarded (``incident.created``, ``incident.updated``, ``incident.resolved``, …) and save.

Verify
------

Create a test incident in Rootly. The event should appear in **Settings → Delivery Log** and on the Robusta timeline.
