Rootly
=======

Forward Rootly alert lifecycle events to Robusta via a Rootly outgoing webhook.

Prerequisites
-------------

* A Robusta account with API access.
* Your Robusta ``account_id``, found in ``generated_values.yaml``.
* A Robusta API key with ``Read/Write`` access to alerts, generated under **Settings → API Keys → New API Key**.
* A Rootly admin able to create outgoing webhooks.

Webhook URL
-----------

.. robusta-code::

    https://api.robusta.dev/webhooks?type=alert&origin=rootly&account_id=<ACCOUNT_ID>

Configure Rootly
----------------

1. In Rootly, go to **Integrations → Webhooks → New Webhook**.
2. Set the **URL** to the webhook URL above.
3. Add a custom header:

   .. code-block::

       Authorization: Bearer <ROBUSTA_API_KEY>

4. Subscribe the webhook to the alert events you want forwarded — at minimum ``alert.created`` and ``alert.resolved``. ``alert.acknowledged`` is also supported and is treated as a still-firing alert.
5. Save. Rootly will start delivering alerts immediately.

Payload
-------

Rootly sends a fixed JSON envelope; no body template is required. The relay extracts the alert summary, status, source system, labels, and timestamps. Severity is read from ``data.labels[]`` (Rootly's ``[{key, value}]`` array) or from the freeform ``data.data`` object if the upstream system propagated it there. The ``data.external_id`` field is used as the deduplication fingerprint so retransmissions of the same upstream alert fold into a single Robusta timeline entry.

Verify
------

Trigger a test alert in Rootly (or wait for the next real alert). The event should appear in **Settings → Delivery Log** and on the Robusta timeline.
