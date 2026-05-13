New Relic
==========

Forward New Relic alerts to Robusta via a New Relic webhook destination.

Prerequisites
-------------

* A Robusta account with API access.
* Your Robusta ``account_id``, found in ``generated_values.yaml``.
* A Robusta API key with ``Read/Write`` access to alerts.
* A New Relic admin able to create webhook destinations.

Webhook URL
-----------

.. code-block::

    https://api.robusta.dev/webhooks?type=alert&origin=newrelic&account_id=<ACCOUNT_ID>

Configure New Relic
-------------------

1. In New Relic, go to **Alerts & AI → Destinations** and add a **Webhook** destination named ``Robusta``.
2. Set the **Endpoint URL** to the webhook URL above.
3. Add a custom header:

   .. code-block::

       Authorization: Bearer <ROBUSTA_API_KEY>

4. Use the default payload template.
5. Create a **Workflow** that routes the desired policy to this destination.

Verify
------

Trigger a test incident in New Relic. The alert should appear on the Robusta timeline.
