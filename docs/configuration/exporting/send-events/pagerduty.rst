PagerDuty
==========

Forward PagerDuty incidents (and AIOps alerts) to Robusta via Generic Webhooks v3.

Prerequisites
-------------

* A Robusta account with API access.
* Your Robusta ``account_id``, found in ``generated_values.yaml``.
* A Robusta API key with ``Read/Write`` access to alerts, generated under **Settings → API Keys → New API Key**.
* A PagerDuty admin able to create webhooks. AIOps Event Orchestration is required to forward full alert-level data.

Webhook URL
-----------

For incidents:

.. code-block::

    https://api.robusta.dev/webhooks?type=incident&origin=pagerduty&account_id=<ACCOUNT_ID>

For AIOps-forwarded alerts:

.. code-block::

    https://api.robusta.dev/webhooks?type=alert&origin=pagerduty&account_id=<ACCOUNT_ID>

Configure PagerDuty
-------------------

1. In PagerDuty, go to **Integrations → Generic Webhooks v3** and click **New Webhook**.
2. Set the **Webhook URL** to the URL above.
3. Add a custom header:

   .. code-block::

       Authorization: Bearer <ROBUSTA_API_KEY>

4. Save. PagerDuty will sign the payload, but Robusta authenticates on the API key alone — the signature is ignored.

For AIOps event-level forwarding, repeat the same steps inside **AIOps → Event Orchestration → Webhook Action** and target the ``type=alert`` URL.

Verify
------

Trigger a test incident in PagerDuty. It should appear in **Settings → Delivery Log** and on the Robusta timeline.
