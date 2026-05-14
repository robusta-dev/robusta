LaunchDarkly
=============

Forward LaunchDarkly feature-flag changes to Robusta so HolmesGPT can
correlate flag flips with alert spikes.

Prerequisites
-------------

* A Robusta account with API access.
* Your Robusta ``account_id``, found in ``generated_values.yaml``.
* A Robusta API key with ``Read/Write`` access to alerts, generated under **Settings → API Keys → New API Key**.

Webhook URL
-----------

.. code-block::

    https://api.robusta.dev/webhooks?type=change&origin=launchdarkly&account_id=<ACCOUNT_ID>

Configure LaunchDarkly
----------------------

In the LaunchDarkly UI:

1. Open **Integrations → Webhooks** and click **Add integration**.
2. Set **URL** to the webhook URL above.
3. Add a custom header ``Authorization`` with value ``Bearer <ROBUSTA_API_KEY>``.
4. Optionally narrow the **Policy** so only flag changes from the
   environments you care about are sent.
5. Save.

LaunchDarkly's default JSON payload is parsed out of the box — no
template is required.

Example Payload
---------------

.. code-block:: json

    {
      "kind": "flag",
      "name": "beta-checkout",
      "title": "LaunchDarkly Flag Change: beta-checkout",
      "titleVerb": "updated",
      "description": "enabled in production",
      "target": {"name": "beta-checkout"},
      "parent": {"name": "production"},
      "previousVersion": {"environments": {"production": {"on": false}}},
      "currentVersion": {"environments": {"production": {"on": true}}},
      "member": {
        "firstName": "Jane",
        "lastName": "Doe",
        "email": "jane@example.com"
      }
    }

The parser produces one ``Issues`` row with ``finding_type =
configuration_change`` plus a ``diff`` evidence row showing the before/after
JSON of the flag in the affected environment, a ``markdown`` summary
block, and the standard ``alert_raw_data`` / ``incoming_event_ref``
evidences.

Test the Integration
--------------------

Trigger a small change to any flag in your LaunchDarkly project. The
event should appear on the Robusta timeline within a few seconds — open
the **Delivery Log** UI to confirm ``parse_status = parsed``.
