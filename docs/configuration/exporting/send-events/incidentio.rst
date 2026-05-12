Incident.io
============

Forward Incident.io incidents to Robusta via an Incident.io outgoing webhook.

Prerequisites
-------------

* A Robusta account with API access.
* Your Robusta ``account_id``, found in ``generated_values.yaml``.
* A Robusta API key with ``Read/Write`` access to alerts.
* Incident.io admin access.

Webhook URL
-----------

.. code-block::

    https://api.robusta.dev/webhooks?type=incident&origin=incidentio&account_id=<ACCOUNT_ID>

Configure Incident.io
---------------------

1. In Incident.io, go to **Settings → Webhooks → New webhook**.
2. Set the **URL** to the URL above.
3. Add a custom HTTP header:

   .. code-block::

       Authorization: Bearer <ROBUSTA_API_KEY>

4. Subscribe to the events you want forwarded (``incident.created``, ``incident.updated``, ``incident.resolved``, …) and save. Incident.io will sign the payload — Robusta ignores the signature and authenticates on the bearer token.

Verify
------

Declare a test incident. The event should appear in **Settings → Delivery Log** and on the Robusta timeline.
