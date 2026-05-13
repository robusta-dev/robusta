PagerDuty
==========

Forward PagerDuty alerts to Robusta via PagerDuty AIOps Event Orchestration.

Prerequisites
-------------

* A Robusta account with API access.
* Your Robusta ``account_id``, found in ``generated_values.yaml``.
* A Robusta API key with ``Read/Write`` access to alerts, generated under **Settings → API Keys → New API Key**.
* An AIOps-enabled PagerDuty plan with admin access to Event Orchestration.

Webhook URL
-----------

.. code-block::

    https://api.robusta.dev/webhooks?type=alert&origin=pagerduty&account_id=<ACCOUNT_ID>

Configure PagerDuty
-------------------

1. In PagerDuty, go to **AIOps → Event Orchestration** and open the orchestration that handles the alerts you want forwarded.
2. Under **Automation → Webhook Actions**, add a new webhook.
3. Set the **Webhook URL** to the URL above.
4. Add a custom header:

   .. code-block::

       Authorization: Bearer <ROBUSTA_API_KEY>

5. Save.

Verify
------

Trigger a test alert in PagerDuty. It should appear in **Settings → Delivery Log** and on the Robusta timeline.
