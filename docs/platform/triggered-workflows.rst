.. _triggered-workflows:

Triggered Workflows
====================

Triggered Workflows let you define a reusable Holmes investigation and run it from any system that can send a webhook — PagerDuty, Jira, Sentry, GitHub Actions, AlertManager, or your own scripts.

Each workflow is a saved prompt plus a target agent. When a webhook arrives, Holmes runs the prompt against the incoming payload and delivers the findings wherever the prompt tells it to.

How It Works
------------

1. You create a workflow in the Robusta UI and get back a webhook URL.
2. Your external system POSTs an event to that URL.
3. Holmes investigates using the tools enabled on the target agent.
4. Holmes delivers the report as instructed in your prompt — a Jira comment, a Slack message, an HTTP callback, or all three.

Robusta does not ship a separate delivery mechanism. **Delivery instructions live in the prompt itself**, and Holmes uses whichever toolsets and MCP servers are already enabled on the agent.

Creating a Workflow
-------------------

In the Robusta UI, open **Automate → Triggered workflows** and click **Create workflow** — the **+** button at the top of the workflow list, or the **Create workflow** button on the intro screen. Start from a template or write your own.

.. list-table::
   :widths: 25 10 65
   :header-rows: 1

   * - Field
     - Required
     - Description
   * - **Title**
     - Yes
     - Names the workflow and titles each investigation it creates.
   * - **Prompt**
     - Yes
     - What Holmes should investigate. End it with a delivery instruction, e.g. *"post the findings as a comment on the same Jira issue"*.
   * - **Enabled**
     - No
     - Defaults to on. A disabled workflow still accepts webhooks, but every event is skipped instead of investigated.
   * - **Agent**
     - Yes
     - The cluster whose Holmes runs the investigation. Agents running an older Holmes are marked ``(outdated)`` and cannot be selected.
   * - **AI Model**
     - No
     - Overrides the default model for this workflow.
   * - **Max daily investigations**
     - Yes
     - Rolling 24-hour cap. Defaults to ``20``, which is also the maximum during beta.
   * - **Create incidents from this workflow**
     - No
     - Groups repeated findings into incidents instead of re-investigating them. See :doc:`/platform/incident-grouping`.
   * - **Filters**
     - No
     - Restricts the workflow to matching payloads. See `Filtering Events`_.

Webhook URL
-----------

Every workflow gets its own URL. Copy it from the workflow page under **Send Events**.

.. robusta-code::

    POST https://api.robusta.dev/webhooks?account_id=<ACCOUNT_ID>&workflow_id=<WORKFLOW_ID>

Query Parameters
----------------

.. list-table::
   :widths: 20 70
   :header-rows: 1

   * - Parameter
     - Description
   * - ``account_id``
     - Your Robusta account ID, found in ``generated_values.yaml``.
   * - ``workflow_id``
     - The workflow to run. Repeat the parameter (``&workflow_id=a&workflow_id=b``) or comma-separate values (``&workflow_id=a,b``) to trigger several workflows from one event. Each value must be a valid UUID.
   * - ``cluster``
     - Optional. Runs the investigation on this agent instead of the one configured on the workflow. See `Targeting a Cluster Per Request`_.
   * - ``type``
     - Optional. Categorizes the event: ``alert``, ``incident``, ``change``, or ``event``. Defaults to ``event``, and any other value is rejected. It does not affect workflow routing — an event carrying a ``workflow_id`` always goes to workflows. See `Limitations`_.
   * - ``token``
     - Optional. Your API key, as an alternative to the ``Authorization`` header. Ignored if an ``Authorization`` header is present. See the warning under `Authentication`_.

Authentication
--------------

Send a Robusta API key with the ``Alerts: Write`` permission. Create one in the Robusta UI under **Settings → API Keys → New API Key**, and use the full ``hint.key`` string exactly as the UI displays it.

.. code-block::

    Authorization: Bearer <API_KEY>

The ``Authorization`` header is the preferred method. For systems that cannot set headers, append the key as a query parameter instead:

.. robusta-code::

    POST https://api.robusta.dev/webhooks?account_id=<ACCOUNT_ID>&workflow_id=<WORKFLOW_ID>&token=<API_KEY>

.. warning::

    Use ``token`` only when the sending system cannot set headers. A key in the query string is recorded wherever URLs are — proxy and access logs, browser history, and observability tooling. Give such keys the ``Alerts: Write`` permission and nothing more, and rotate the key in **Settings → API Keys** if the URL is ever exposed.

Example Request
---------------

.. robusta-code:: bash

    curl --location --request POST \
      'https://api.robusta.dev/webhooks?account_id=ACCOUNT_ID&workflow_id=WORKFLOW_ID' \
      --header 'Authorization: Bearer API_KEY' \
      --header 'Content-Type: application/json' \
      --data-raw '{ "incident": { "severity": "P1", "title": "Checkout latency" } }'

Response
--------

A successful request returns ``200`` with the ID of the stored event:

.. code-block:: json

    { "id": "8f1b...e21" }

Errors:

* ``400`` — missing ``account_id``, invalid ``type``, or a ``workflow_id`` that is not a UUID. Malformed IDs are rejected before authentication, and no workflow in the request runs.
* ``401`` — missing, malformed, or unknown API key.
* ``403`` — valid API key without the ``Alerts: Write`` permission.
* ``429`` — rate limit exceeded (300 requests per 5-minute window per account).
* ``503`` — transient storage failure. Retry.

.. warning::

    ``200`` only means the event was accepted for processing. Workflows that are disabled, filtered out, over their daily limit, or referenced by an unknown ID are all reported as ``200`` and skipped later. Check the **Events** table on the workflow page to see what actually happened.

.. _triggered-workflows-cluster-param:

Targeting a Cluster Per Request
-------------------------------

Every workflow has an **Agent** — the cluster whose Holmes runs the investigation. Add ``cluster=<CLUSTER_NAME>`` to the webhook URL to override it for a single request:

.. robusta-code::

    POST https://api.robusta.dev/webhooks?account_id=<ACCOUNT_ID>&workflow_id=<WORKFLOW_ID>&cluster=prod-us-east-1

This lets one workflow definition serve many clusters. Instead of duplicating a workflow per cluster, configure the webhook in each cluster's monitoring system with a different ``cluster`` value.

* ``cluster`` always wins over the workflow's configured **Agent**.
* When ``cluster`` is omitted, the workflow's **Agent** is used.
* When neither is set, the event is skipped as ``misconfigured: missing cluster_name``.
* The value is the cluster name as it appears in the Robusta UI. It is not validated — a typo produces an investigation that never runs.

The same parameter works on alert webhooks, where it sets the cluster of the resulting alert. See the :doc:`Send Events API </configuration/exporting/send-events-api>`.

Filtering Events
----------------

A workflow with no filter investigates every event it receives. To narrow it down, set both **Key** and **Value matches regex** under **Filters**.

Robusta walks the payload and collects the value of every key with that exact name, at any nesting depth, including inside arrays. If any collected value matches the regex, the workflow runs.

With key ``severity`` and regex ``^(P1|P2)$``:

.. code-block:: json

    { "incident": { "severity": "P1" } }

runs the workflow, while

.. code-block:: json

    { "incident": { "severity": "P3" } }

skips it.

Filter behavior:

* **Both fields are required together.** Setting only one blocks saving.
* **Key names match exactly and are case-sensitive.** There is no dot-path or wildcard syntax — ``severity`` matches a ``severity`` key anywhere in the payload, including one you did not intend.
* **The regex is unanchored.** ``P1`` also matches ``P10`` and ``NOT-P1``. Use ``^…$`` for an exact match.
* **Patterns are evaluated as Python regular expressions.** The form validates using the browser's regex engine, so a pattern that is valid in JavaScript but not in Python is silently treated as never matching.
* **Only scalar values are compared.** Booleans become ``true``/``false``, numbers their text form, ``null`` becomes ``null``. Objects and arrays never match.
* **A filtered workflow needs valid JSON.** If the body is not parseable JSON, there is nothing to walk and the workflow is skipped.

Delivering Results
------------------

Tell Holmes how to deliver the report at the end of your prompt. For example:

.. code-block:: text

    A Jira webhook payload is available as the trigger context. Read the issue key,
    summary and description, investigate the described problem using the available
    tools, and post the findings back as a comment on the same Jira issue.
    Add a comment only; do not edit any other field.

Holmes can only deliver through tools that are enabled on the target agent — Slack through your Robusta notification settings, Jira, PagerDuty and GitHub through their MCP servers, and so on. If the prompt has no delivery instruction, or the necessary integration is not enabled, the report exists only inside the run's conversation in the Robusta UI.

Daily Investigation Limit
-------------------------

Each workflow has a **Max daily investigations** cap over a rolling 24 hours, set to ``20`` by default. The cap counts only events that actually start an investigation; once it is reached, further events that would need one are skipped until the window rolls forward. Events that an incident matcher attaches to an existing incident do not consume the budget and are not blocked by it — see :doc:`/platform/incident-grouping`.

The workflow page shows **Investigations Today** against the limit.

Monitoring Runs
---------------

The workflow page shows total and daily investigation counts, a 7-day chart, the most recent run, and how many events were skipped.

**Events** lists incoming webhooks, including ones that were not investigated, with an outcome, the time received, and a preview of the payload. Clicking a row opens the event's full payload; for events that produced an investigation, the row's **Investigation** link opens the full conversation, exactly like a Holmes chat.

.. list-table::
   :widths: 35 65
   :header-rows: 1

   * - Outcome
     - Meaning
   * - ``Investigated`` / ``Investigating``
     - The event produced a run.
   * - ``Investigation failed`` / ``Investigation timed out`` / ``Investigation stopped``
     - The investigation started but did not finish successfully.
   * - ``Attached to incident``
     - An auto-attach rule matched, so the event joined an existing incident instead of being investigated. Only appears when **Create incidents from this workflow** is on. See :doc:`/platform/incident-grouping`.
   * - ``not found``
     - No workflow with that ID exists on this account. Usually a deleted workflow whose webhook is still configured somewhere.
   * - ``disabled``
     - The workflow exists but is switched off.
   * - ``filtered``
     - The payload did not match the workflow's filter.
   * - ``misconfigured: missing cluster_name``
     - No **Agent** on the workflow and no ``cluster`` parameter on the request.
   * - ``LLM investigation limit reached``
     - The daily cap was hit. The note shows the count and the limit.
   * - ``Parse error`` / ``Did not investigate``
     - The event could not be parsed, or produced no run and no specific skip reason.

When webhooks arrive for a workflow that no longer exists, a red **N events with no workflow** entry appears at the top of the workflow list and opens a view of them. It covers only events received in the last 24 hours.

Limitations
-----------

* **A webhook with a** ``workflow_id`` **is not parsed as an alert.** Even with ``type=alert``, an event carrying a workflow ID is only fanned out to workflows — no alert or issue is created from it. Use two separate webhook calls if you need both.
* **Investigations are shared and unattributed.** Runs do not use the creator's personal integrations, and every account member with access to the cluster can see them.
* **Deleting a workflow deletes its investigations.** Webhooks still pointing at that ID then show up as ``not found``.
* **The Events table shows only the most recent 200 events, and the page loads only the most recent 100 investigations.** That capped run list drives the 7-day chart and the **Last Investigation** and **Investigations Today** boxes, while **Total Investigations** and **Events Skipped** are exact. On busy workflows the numbers will not agree.
