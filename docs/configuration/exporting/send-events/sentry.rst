Sentry
=======

Forward Sentry alerts and issues to Robusta via Sentry's Internal
Integration.

Sentry can send events to Robusta in two different ways. Use either
one, or enable both on the same integration:

* :ref:`Issue Lifecycle Webhook <sentry-path-issue-lifecycle>` fires
  on every issue created / resolved / assigned / archived /
  unresolved across the org. Lighter payload (no per-event details,
  no event-level tags), zero alert-rule plumbing. Use this when you
  want every Sentry issue on the Robusta timeline.
* :ref:`Send alert webhook <sentry-path-alert-rule>` fires only when
  a Sentry Issue Alert Rule (or Metric Alert Rule) triggers and lists
  Robusta as one of its actions. Richer payload (event detail, rule
  name, and all tags attached to the event). Use this when you want
  rule-driven, throttled alerts.

Prerequisites
-------------

* A Robusta account with API access.
* Your Robusta ``account_id``, found in ``generated_values.yaml`` or
  under **Settings → Workspace** in the Robusta UI.
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

.. note::

   Sentry Internal Integrations **do not let you add custom outgoing
   HTTP headers** (the only auth header Sentry sends is its own
   ``Sentry-Hook-Signature``). The Robusta API key therefore goes in
   the ``&token=`` URL parameter rather than an ``Authorization``
   header.

Create the Custom Integration
-----------------------------

1. In Sentry, navigate to **Settings → Integrations → Custom
   Integrations**.
2. Click **Create New Integration** in the top right.
3. In the **Choose Integration Type** dialog, select **Internal
   Integration** and click **Next**.
4. **Name**: ``Robusta`` (or ``Robusta Prod Alerts``, etc. — this is
   only for display in Sentry).
5. **Webhook URL**: paste the URL from the previous section.

Then configure
:ref:`Issue Lifecycle Webhook <sentry-path-issue-lifecycle>`,
:ref:`Send alert webhook <sentry-path-alert-rule>`, or both, and save
the integration at the end.

.. _sentry-path-issue-lifecycle:

Issue Lifecycle Webhook
-----------------------

Subscribe to lifecycle events so every Sentry issue lands on the
Robusta timeline.

In the **PERMISSIONS** section of the same form:

1. **Issue & Event**: set to **Read**.

Then in the **WEBHOOKS** section:

2. Tick **only** the ``issue`` checkbox (sub-events: ``created``,
   ``resolved``, ``assigned``, ``archived``, ``unresolved``).

.. warning::

   Do **not** enable the ``error`` checkbox. It fires on every
   individual error event (not per issue) — a noisy service will
   generate far more webhook traffic than the issue checkbox does.

3. Click **Save Changes** at the bottom of the form. The integration
   now appears under **INTERNAL INTEGRATIONS** on the Custom
   Integrations list page.

.. _sentry-path-alert-rule:

Send alert webhook
------------------

Register Robusta as a selectable action inside Sentry Issue Alert and
Metric Alert rules so the integration receives the rich
``event_alert`` payload only when a rule fires. Two parts: configure
the integration, then add Robusta to an existing alert rule.

Configure the integration
~~~~~~~~~~~~~~~~~~~~~~~~~

In the **INTERNAL INTEGRATION DETAILS** section of the same form:

1. **Alert Rule Action**: tick this checkbox.

2. **Schema**: paste the following JSON so Robusta appears in
   Sentry's alert rule action picker.

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
                  "type": "select",
                  "label": "Destination",
                  "name": "destination",
                  "options": [["robusta", "Robusta"]]
                }
              ]
            }
          }
        ]
      }

   The ``title`` is the action label that shows up inside Sentry's
   alert rule editor. The schema is what tells Sentry how to render
   the integration in the picker — without it, Robusta won't appear
   in the "Send a notification via an integration" dropdown.

Then in the **PERMISSIONS** section:

3. **Alerts**: set to **Read**.

4. Click **Save Changes** at the bottom of the form. The integration
   now appears under **INTERNAL INTEGRATIONS** on the Custom
   Integrations list page.

Add Robusta to an existing alert rule
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The integration is now selectable in alert rules, but until a rule
references it Sentry won't POST anything. For each Sentry alert rule
you want to forward to Robusta:

1. In the project that owns the rule, open **Alerts → Alert Rules**
   and click the rule you want to forward.
2. Under **Then perform these actions**, click **Add action** and
   select **Send a notification via an integration → Robusta**.
3. The "Destination" dropdown the schema declared appears here;
   leave it at "Robusta".
4. **Save** the rule.

When the rule's conditions match, Sentry POSTs the ``event_alert``
payload to Robusta, and the rule name shows up as the Robusta
aggregation key.

.. _sentry-verify:

Verify
------

Trigger an event end-to-end to confirm the pipeline:

* **Path A**: in Sentry, pick any existing issue → click
  **Resolve** → then **Unresolve**. Two ``issue`` webhooks fire
  back-to-back.
* **Path B**: trigger an Issue Alert Rule that targets the Robusta
  integration (or set the rule to "An event is seen" with no filters
  and trigger any error in the app).

Then:

1. Open the integration's **Dashboard** tab in Sentry — each POST
   should show HTTP **200** from Robusta.
2. Open **Settings → Delivery Log** in the Robusta UI — the event
   should appear with ``parse_status=parsed``.
3. Open the Robusta timeline — the Sentry-sourced row should land
   within a few seconds.

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

If the dashboard shows **no recent requests** even though you
triggered an event:

* For **Path A**, verify the ``issue`` checkbox under **Webhooks** is
  enabled and the integration is saved.
* For **Path B**, verify the **Alert Rule Action** checkbox is on,
  the **Schema** is saved, and the alert rule in your project lists
  Robusta as one of its actions.

If the dashboard shows **200 responses but nothing appears in the
Robusta timeline**, open the Robusta **Delivery Log** and look for
rows with ``origin=sentry`` and ``parse_status=failed`` — the
``parser_error`` column tells you which field the parser couldn't
read.
