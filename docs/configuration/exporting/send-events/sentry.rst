Sentry
=======

Forward Sentry alerts and issues to Robusta via Sentry's Internal
Integration.

Sentry can send events to Robusta in two different ways. Use either
one, or enable both on the same integration:

* :ref:`sentry-path-issue-lifecycle` — fires on every issue created /
  resolved / assigned / archived / unresolved across the org. Lighter
  payload (no per-event details, no event-level tags), zero
  alert-rule plumbing. Use this when you want every Sentry issue on
  the Robusta timeline.
* :ref:`sentry-path-alert-rule` — fires only when a Sentry Issue
  Alert Rule (or Metric Alert Rule) triggers and lists Robusta as one
  of its actions. Richer payload (event detail, rule name, and all
  tags attached to the event). Use this when you want rule-driven,
  throttled alerts.

The recommended setup uses both on a single integration: subscribe to
the issue lifecycle webhook *and* register the integration as an alert
rule action.

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

Start a new Internal Integration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. In Sentry, navigate to **Settings → Integrations → Custom
   Integrations**.
2. Click **Create New Integration** in the top right.
3. In the **Choose Integration Type** dialog, select **Internal
   Integration** and click **Next**.

4. **Name**: ``Robusta`` (or ``Robusta Prod Alerts``, etc. — this is
   only for display in Sentry).
5. **Webhook URL**: paste the URL from the previous section.

6. **Issue & Event**: set to **Read**.
7. **Alerts**: set to **Read** (only needed if you'll set up
   :ref:`sentry-path-alert-rule`; harmless to grant either way).
8. Leave every other permission row at **No Access**.

Save the base integration before configuring either webhook path:

9. Click **Save Changes** at the bottom of the form. The integration
   now appears under **INTERNAL INTEGRATIONS** on the Custom
   Integrations list page with a **Dashboard** button next to it —
   that dashboard is the primary debugging surface (see
   :ref:`troubleshooting <sentry-troubleshooting>`).

.. _sentry-path-issue-lifecycle:

Path A — Issue Lifecycle Webhook
---------------------------------

Sentry POSTs to the Webhook URL on every issue lifecycle transition
(``created`` / ``resolved`` / ``assigned`` / ``archived`` /
``unresolved``). This is the simpler path: no schema, no alert rules,
every issue lands on the Robusta timeline automatically.

Open the integration you just created and scroll to the **WEBHOOKS**
section:

1. Tick **only** the ``issue`` checkbox (sub-events: ``created``,
   ``resolved``, ``assigned``, ``archived``, ``unresolved``).
2. Leave ``error``, ``comment``, ``seer``, and ``preprod_artifact``
   unchecked.
3. Click **Save Changes**.

.. warning::

   Do **not** enable the ``error`` checkbox. It fires on every
   individual error event (not per issue), which will exhaust
   Robusta's 300-requests-per-5-minutes rate limit on any non-trivial
   service. The relay parser also doesn't recognise the ``error``
   webhook payload shape, so enabled-``error`` traffic lands as
   ``parse_status=failed`` rows.

That's the entire Path A setup. Skip ahead to :ref:`Verify
<sentry-verify>` to test it, or continue to Path B to layer
alert-rule routing on top.

.. _sentry-path-alert-rule:

Path B — Alert Rule Action
--------------------------

This path makes Robusta selectable as an action inside Sentry Issue
Alert and Metric Alert rules. Sentry POSTs only when one of those
rules fires, and the webhook carries the event detail plus the rule
name as the aggregation key.

Two parts: register the integration as an alert action, then create
the alert rule that uses it.

Register Robusta as an alert action
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Open the integration and scroll back up to **INTERNAL INTEGRATION
DETAILS**:

1. **Alert Rule Action**: tick this checkbox. The notification
   destination is the **Webhook URL** you saved earlier.

   .. note::

      The checkbox is locked until **Webhook URL** is filled in —
      Sentry's tooltip reads
      *"Cannot enable alert rule action without a webhook url"*. If
      you completed the shared setup above the URL is already there.

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

   The ``title`` is what shows up as the action label inside Sentry's
   alert rule editor. The ``Alert Rule Action`` checkbox toggles the
   feature on, but Sentry uses this schema to know *how* to render
   the integration in the picker — without it, Robusta won't appear
   in the "Send a notification via an integration" dropdown.

   .. note::

      Sentry's schema validator requires ``required_fields`` to
      contain **at least one element** — an empty array fails with
      *"[] is too short for element of type 'alert-rule-action'"*.
      The single ``select`` field above is a placeholder that mirrors
      Sentry's `documented schema example
      <https://docs.sentry.io/integrations/integration-platform/ui-components/alert-rule-action/>`_:
      users configuring an alert rule see a "Destination" dropdown
      whose only option is "Robusta", so there's nothing to type and
      no risk of misconfiguration. Robusta ignores
      ``data.issue_alert.settings`` server-side, so the value doesn't
      affect ingestion.

      A ``text`` field would also satisfy the constraint, but Sentry
      additionally restricts ``text``/``textarea`` defaults to
      ``issue.title`` or ``issue.description`` only, which is a more
      brittle pattern.

   .. note::

      Sentry appends the schema's ``uri`` path to the webhook URL
      host when an alert rule fires, so the path component of the
      **Webhook URL** field (``/webhooks``) must match the schema
      ``uri``. Query parameters in the Webhook URL are preserved.

3. Click **Save Changes**.

Create the Sentry alert rule
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The integration is now selectable in alert rules, but until a rule is
actually configured against it Sentry won't POST anything. For each
project that should forward to Robusta:

4. Open **Alerts → Create Alert** and choose **Issues**.
5. Configure your conditions and filters as usual.
6. Under **Then perform these actions**, click **Add action** and
   select **Send a notification via an integration → Robusta**.
7. The "Destination" dropdown the schema declared appears here; leave
   it at "Robusta".
8. Save the rule.

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
