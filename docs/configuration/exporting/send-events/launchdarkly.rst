LaunchDarkly
=============

Forward LaunchDarkly flag and segment changes to Robusta as ``change`` events.

Prerequisites
-------------

* A Robusta account with API access.
* Your Robusta ``account_id``, found in ``generated_values.yaml``.
* A Robusta API key with ``Read/Write`` access to alerts.
* LaunchDarkly admin access.

Webhook URL
-----------

.. code-block::

    https://api.robusta.dev/webhooks?type=change&origin=launchdarkly&account_id=<ACCOUNT_ID>

Configure LaunchDarkly
----------------------

1. In LaunchDarkly, go to **Integrations → Webhooks → Add integration**.
2. Set the **URL** to the URL above.
3. Optionally restrict the events with a **Policy filter** (for example, only flag updates in production).
4. LaunchDarkly does not let you add an ``Authorization`` header; instead enable **HMAC signing** (Robusta ignores it) and append ``&token=<ROBUSTA_API_KEY>`` to the URL.

   .. warning::

      Query-parameter tokens can be exposed in proxy and server access logs and in browser history. Prefer HMAC signing where it is supported end-to-end. If you must use a URL token, use a dedicated, narrowly scoped Robusta API key with only the permissions this integration requires, and rotate it on a regular cadence so a leaked URL has a bounded blast radius.

Verify
------

Toggle a feature flag in LaunchDarkly. The event should appear in **Settings → Delivery Log** and on the Robusta timeline as a ``change`` event.
