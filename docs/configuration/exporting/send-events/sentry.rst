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
* Sentry **Owner** or **Manager** role on the org (lower roles can't
  create Custom Integrations).

Webhook URL
-----------

.. robusta-code::

    https://api.robusta.dev/webhooks?type=alert&origin=sentry&account_id=<ACCOUNT_ID>&token=<ROBUSTA_API_KEY>

Replace ``<ACCOUNT_ID>`` with your Robusta account id and
``<ROBUSTA_API_KEY>`` with the API key you just generated.

Create the Custom Integration
-----------------------------

Sentry's "Internal Integration" lives under **Custom Integrations** in
the current UI; the two names refer to the same feature.

Open the list page
~~~~~~~~~~~~~~~~~~

1. In Sentry, navigate to **Settings → Integrations → Custom
   Integrations** (direct link:
   ``https://<your-org>.sentry.io/settings/custom-integrations/``).
2. Click **Create New Integration** in the top right.
3. In the **Choose Integration Type** dialog, select **Internal
   Integration** and click **Next**.

Fill in "Internal Integration Details"
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In the **INTERNAL INTEGRATION DETAILS** section:

4. **Name**: ``Robusta`` (or ``Robusta Prod Alerts``, etc. — this is
   only for display in Sentry).
5. **Webhook URL**: paste the URL from the previous section.
6. **Alert Rule Action**: enable this checkbox if you want the
   integration to be selectable inside Sentry Issue Alert and Metric
   Alert rules. The notification destination is the **Webhook URL**
   you just filled in. Leave it disabled if you only want the issue
   lifecycle webhook.

   .. note::

      The checkbox stays locked until **Webhook URL** (step 5) is
      filled in — Sentry's tooltip reads
      *"Cannot enable alert rule action without a webhook url"*.
      Fill the Webhook URL first, then tick this checkbox.

7. **Schema** *(required for the alert-rule path; leave blank if you
   only want the issue lifecycle webhook)*: paste the following JSON
   so Robusta appears in Sentry's alert rule action picker.

   .. code-block:: json

      {
        "elements": [
          {
            "type": "alert-rule-action",
            "title": "Send to Robusta",
            "settings": {
              "type": "alert-rule-settings",
              "uri": "/webhooks",
              "required_fields": [
                {
                  "type": "text",
                  "name": "tags",
                  "label": "Tags",
                  "default": "sentry"
                }
              ]
            }
          }
        ]
      }

   The ``title`` is what shows up as the action label inside Sentry's
   alert rule editor. The ``Alert Rule Action`` checkbox in step 6
   toggles the feature on, but Sentry uses this schema to know *how*
   to render the integration in the picker — without it, Robusta
   won't appear in the "Send a notification via an integration"
   dropdown.

   .. note::

      Sentry's schema validator rejects ``alert-rule-action`` elements
      whose ``required_fields`` array is empty
      (*"[] is too short for element of type 'alert-rule-action'"*).
      The ``tags`` field above is a placeholder so the schema saves
      cleanly; users configuring an alert rule will see a "Tags" text
      input pre-filled with ``sentry`` and can leave it as-is. Robusta
      ignores ``data.issue_alert.settings`` server-side, so the value
      doesn't affect ingestion.

   .. note::

      Sentry appends the schema's ``uri`` path to the webhook URL host
      when an alert rule fires, so the path component of the **Webhook
      URL** field above (``/webhooks``) must match the schema ``uri``.
      Query parameters in the Webhook URL are preserved.

8. **Overview** and **Authorized JavaScript Origins**: leave both
   blank.

Grant permissions
~~~~~~~~~~~~~~~~~

In the **PERMISSIONS** section, change the dropdowns:

9. **Issue & Event**: set to **Read**.
10. **Alerts**: set to **Read** (only required if you enabled Alert
    Rule Action in step 6).
11. Leave every other permission row at **No Access**.

Subscribe to webhook events
~~~~~~~~~~~~~~~~~~~~~~~~~~~

In the **WEBHOOKS** section:

12. Tick **only** the ``issue`` checkbox (sub-events: ``created``,
    ``resolved``, ``assigned``, ``archived``, ``unresolved``). Leave
    ``error``, ``comment``, ``seer``, and ``preprod_artifact``
    unchecked.

    .. warning::

       Do **not** enable the ``error`` checkbox. It fires on every
       individual error event (not per issue), which will exhaust
       Robusta's 300-requests-per-5-minutes rate limit on any
       non-trivial service. The relay parser also doesn't recognise
       the ``error`` webhook payload shape, so enabled-``error``
       traffic lands as ``parse_status=failed`` rows.

Save
~~~~

13. Click **Save Changes** at the bottom of the form. The integration
    now appears under **INTERNAL INTEGRATIONS** on the Custom
    Integrations list page with a **Dashboard** button next to it —
    that dashboard is the primary debugging surface (see
    :ref:`troubleshooting <sentry-troubleshooting>`).

Wire up an Issue Alert Rule (optional)
--------------------------------------

Skip this section if you only want the issue lifecycle webhook
behavior — the integration is already live after step 13.

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

.. _sentry-troubleshooting:

Troubleshooting
---------------

Sentry exposes its own delivery history on the Custom Integration's
**Dashboard** tab — open the integration from **Settings → Integrations
→ Custom Integrations → Robusta** and switch to **Dashboard**. The
dashboard lists every outgoing webhook with the HTTP status code
Robusta returned, the timestamp, the request body Sentry sent, and the
response body Robusta replied with. Always start debugging here — it
tells you whether the problem is on Sentry's side (no requests showing
up) or Robusta's side (requests present but non-200).

Common responses and what they mean:

.. list-table::
   :header-rows: 1
   :widths: 12 30 58

   * - Status
     - Meaning
     - Fix
   * - **200**
     - Robusta accepted the event.
     - If you don't see it on the timeline shortly after, check the
       Robusta **Delivery Log** for parse failures.
   * - **400**
     - Missing or invalid query parameter.
     - Re-check ``account_id``, ``origin=sentry``, and ``type=alert``
       in the Webhook URL.
   * - **401**
     - API key rejected.
     - The ``token`` in the URL is wrong, expired, or not scoped to the
       same ``account_id``. Regenerate the API key with
       ``Read/Write`` access to alerts and update the Webhook URL.
   * - **429**
     - Rate limit exceeded.
     - More than 300 requests in 5 minutes from this account. Throttle
       the Sentry alert rule or unsubscribe from the high-volume
       ``error`` webhook event.
   * - **5xx**
     - Robusta-side failure.
     - Open the Robusta **Delivery Log** for the event id Sentry
       displays in the response body; if it isn't there, contact
       Robusta support with the request id from the Sentry dashboard.

If the dashboard shows **no recent requests** even though you triggered
an event, the integration isn't subscribed to the right webhook:
verify that the ``issue`` checkbox under **Webhooks** is enabled
(``error`` is not needed — see the note in the previous section), and
that the integration is **installed** to the organization, not just
saved as a draft.

If the dashboard shows **200 responses but nothing appears in the
Robusta timeline**, open the Robusta **Delivery Log** and look for
rows with ``origin=sentry`` and ``parse_status=failed`` — the
``parser_error`` column tells you which field the parser couldn't
read.

