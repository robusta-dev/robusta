Splunk
=======

Forward Splunk alerts to Robusta via a Splunk webhook alert action.

Prerequisites
-------------

* A Robusta account with API access.
* Your Robusta ``account_id``, found in ``generated_values.yaml``.
* A Robusta API key with ``Read/Write`` access to alerts.
* Splunk admin access to define alert actions.

Webhook URL
-----------

.. code-block::

    https://api.robusta.dev/webhooks?type=alert&origin=splunk&account_id=<ACCOUNT_ID>

Splunk's built-in **Webhook** alert action does not support custom headers. Authenticate via the URL:

.. code-block::

    https://api.robusta.dev/webhooks?type=alert&origin=splunk&account_id=<ACCOUNT_ID>&token=<ROBUSTA_API_KEY>

Configure Splunk
----------------

1. Open or create a Splunk saved search and choose **Add Actions → Webhook**.
2. Set the **URL** to the URL above.
3. Save the search. Splunk will POST the search results to Robusta whenever the alert fires.

For environments where you control the Splunk app, use the **Webhook Alert Action** plugin to send an ``Authorization: Bearer <ROBUSTA_API_KEY>`` header instead of the URL token.

Verify
------

Trigger the saved search manually. The event should appear in **Settings → Delivery Log** and on the Robusta timeline.
