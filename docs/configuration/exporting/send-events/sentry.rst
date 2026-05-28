Sentry
=======

Forward Sentry alerts to Robusta via Sentry's Internal Integration.

Sentry's Internal Integrations expose two webhook surfaces. Pick the one
that matches what you want forwarded:

* **Issue Alert webhook** — fires only when a Sentry Issue Alert Rule
  triggers. Includes the rule name, the offending event, and any
  Kubernetes tags you've attached. Use this when you only want
  rule-driven alerts.
* **Issue lifecycle webhook** — fires on every issue created / resolved
  / archived in the org. Lighter payload (no per-event details, no k8s
  subject), but zero alert-rule plumbing. Use this when you want every
  Sentry issue on the Robusta timeline.

The recommended setup uses both: register the integration as an alert
rule action *and* subscribe to issue lifecycle webhooks.

.. note::

   Sentry Internal Integrations **do not let you add custom outgoing
   HTTP headers** (the only auth header Sentry sends is its own
   ``Sentry-Hook-Signature``). Pass the Robusta API key via the
   ``&token=`` URL parameter instead.

Prerequisites
-------------

* A Robusta account with API access.
* Your Robusta ``account_id``, found in ``generated_values.yaml``.
* A Robusta API key with ``Read/Write`` access to alerts, generated
  under **Settings → API Keys → New API Key**.
* Sentry org-level access to install Internal Integrations.

Webhook URL
-----------

.. robusta-code::

    https://api.robusta.dev/webhooks?type=alert&origin=sentry&account_id=<ACCOUNT_ID>&token=<ROBUSTA_API_KEY>

Replace ``<ACCOUNT_ID>`` with your Robusta account id and
``<ROBUSTA_API_KEY>`` with the API key you just generated.

Create the Internal Integration
-------------------------------

1. In Sentry, go to **Settings → Developer Settings → New Internal
   Integration**.
2. **Name**: ``Robusta``.
3. **Webhook URL**: paste the URL from above.
4. **Permissions**: grant **Issue & Event: Read**.
5. **Webhooks**: enable the ``issue`` checkbox. Sentry will POST to
   the webhook URL whenever an issue is created, resolved, assigned,
   archived, or unresolved.
6. **Schema** *(optional, only needed if you want Sentry Alert Rules to
   target Robusta)*: paste the following JSON to register the
   integration as an Alert Rule Action.

   .. code-block:: json

      {
        "elements": [
          {
            "type": "alert-rule-action",
            "title": "Send to Robusta",
            "settings": {
              "type": "alert-rule-settings",
              "uri": "/webhooks",
              "required_fields": []
            }
          }
        ]
      }

7. Click **Save Changes**, then **Install** the integration to your
   organization.

.. note::

   Sentry appends the schema's ``uri`` path to the webhook URL host
   when an alert rule fires, so the path component of the **Webhook
   URL** field above (``/webhooks``) must match the schema ``uri``.
   Query parameters in the Webhook URL are preserved.

Wire up an Issue Alert Rule (optional)
--------------------------------------

Skip this section if you only want the issue lifecycle webhook
behavior — the integration is already live after step 7.

To route a specific Sentry alert rule through Robusta:

1. In each Sentry project, open **Alerts → Create Alert** and choose
   **Issues**.
2. Configure your conditions and filters as usual.
3. Under **Then perform these actions**, select **Send a notification
   via an integration** and pick ``Robusta``.
4. Save the rule. When it fires, Sentry POSTs the event_alert payload
   to Robusta, and the rule name shows up as the Robusta aggregation
   key.

Verify
------

* Resolve and re-open a Sentry issue (lifecycle webhook), or
* Trigger an Issue Alert Rule that targets the Robusta integration
  (alert-rule-action webhook).

Open **Settings → Delivery Log** in the Robusta UI — the event should
appear there with parse status ``parsed``, and the corresponding row
should land on the Robusta timeline.
