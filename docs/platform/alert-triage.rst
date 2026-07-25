.. _alert-triage:

Alert Triage
=============

Alert Triage investigates your alerts with AI and tells you which ones matter. For each alert, Holmes gathers evidence from your connected data sources and returns a root cause, a suggested fix, a priority, and the team that should own it.

Open **Alerts → Triage** in the Robusta UI to see triaged alerts and the backlog of alerts waiting to be investigated.

The Triage Pipeline
-------------------

Alerts move through the pipeline shown at the top of the Triage page:

1. **Alert sources** — alerts arrive from AlertManager, Datadog, PagerDuty, and other sources via the :doc:`Send Events API </configuration/exporting/send-events-api>`.
2. **Queued** — a new alert is queued for investigation.
3. **Investigating** — Holmes is running.
4. **Triage** — Holmes has written its findings back to the alert.
5. **Priority** — the alert is bucketed as Urgent, High, Medium, or Low.
6. **Destinations** — the findings are delivered wherever you configured.

**Queued**, **Investigating**, **Backlog**, and the **Priority** buckets are clickable filters. Clicking **Alert sources**, **Triage**, or **Destinations** instead opens **Pipeline Settings** on the matching tab.

What Holmes Produces
--------------------

Every completed investigation records:

* **What happened** — a summary and a short timeline of events.
* **Root cause analysis** — the reasoning and evidence behind the conclusion.
* **How to fix** — the recommended remediation.
* **Priority** — Holmes classifies urgency internally as ``Urgent``, ``Not Urgent``, ``Noise``, or ``Duplicate``. The UI surfaces this as the **Priority** column: ``Urgent``, ``High``, ``Medium``, or ``Low``. When the alert is linked to an incident, the incident's own priority is shown instead.
* **Team** — the team that should own the alert, with the reason for the assignment.

Holmes checks for duplicates first. When an alert is a duplicate of one it already investigated, it says so and stops instead of repeating the work.

Enabling Automatic Triage
-------------------------

Automatic triage is **off by default**. Turn it on under **Alerts → Triage → Settings → Triage Settings** — the **Settings** button in the page header opens the **Pipeline Settings** dialog.

.. list-table::
   :widths: 30 15 55
   :header-rows: 1

   * - Setting
     - Default
     - Description
   * - **Triage Automatically**
     - ``Off``
     - Investigates every newly firing alert without anyone clicking. When off, you can still investigate alerts manually.
   * - **Daily auto-investigation limit**
     - ``20``
     - Maximum automatic investigations in a rolling 24-hour window. ``20`` is also the maximum during beta.
   * - **Default agent**
     - *(none)*
     - The agent that investigates alerts with no cluster of their own. See `Choosing the Agent`_.
   * - **Create incidents from investigations**
     - ``Off``
     - Lets investigations group related alerts into incidents. See :doc:`/platform/incident-grouping`.

.. note::

    **Create incidents from investigations** is independent of **Triage Automatically**. With automatic triage off, manual investigations still create and update incidents.

Investigating Manually
----------------------

Click **Investigate** on any alert, or select several and investigate them in bulk. Manual investigations ignore both the **Triage Automatically** switch and the daily limit, and they do not count toward it. They still need an eligible agent.

**Re-investigate** discards the previous findings and runs again. While it runs, the alert temporarily moves back to the backlog.

Choosing the Agent
------------------

Investigations run on the agent belonging to the alert's cluster. Two cases need a **Default agent**:

* Alerts that arrive without a cluster are recorded under the cluster ``external``.
* Alerts whose cluster has no Holmes agent connected.

In both cases Robusta reroutes the investigation to the **Default agent**. Set one if alerts are queued but never investigated.

The default agent only decides *where* the investigation runs — the alert keeps its own cluster for display and filtering.

.. warning::

    With no **Default agent** configured, these alerts are skipped rather than left queued, and the two cases record different reasons:

    * Alerts with no cluster of their own are marked ``Skipped`` with the reason ``no eligible cluster (external/unknown, no fallback)``.
    * Alerts on a cluster with no connected agent are marked ``Skipped`` with the reason ``cluster <name> does not support realtime conversations``.

The second reason is also what you get when the agent on that cluster is running a Holmes too old to support realtime conversations. Check whether the cluster has a connected agent before upgrading anything.

Tailoring the Results
---------------------

Under **Pipeline Settings**:

* **Triage Settings** — the switches above.
* **Teams** — the teams Holmes may assign alerts to, each with a description. Without any, everything is assigned to a synthetic ``General`` team.
* **Destinations** — a two-step setup, and both steps are required:

  1. **Give Holmes a messaging tool.** The tab shows the connection status of **Slack** and **Microsoft Teams**. Any other MCP server or data source that can send messages works too, and is configured under Data Sources.
  2. **Tell Holmes what to do after the investigation.** Free-text instructions appended to every investigation prompt, for both automatic and manual runs — which channel to notify and when, or extra context about your environment.

.. warning::

    Instructions alone deliver nothing. With no messaging tool connected, Holmes has no way to send the findings and reports no error.

Urgency classification follows a built-in set of rules:

* ``Urgent`` — active customer impact, data loss risk, or security exposure.
* ``Not Urgent`` — a real issue that can wait, such as a non-critical workload with no immediate user impact.
* ``Noise`` — no meaningful business impact: false positives, test or staging workloads, and known-benign conditions.

These rules are not editable from the UI.

Alert Statuses
--------------

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - Status
     - Meaning
   * - **Not triaged**
     - In the backlog. No investigation has run.
   * - **Queued**
     - Waiting for an agent to pick it up.
   * - **Investigating**
     - Holmes is running.
   * - **Triaged**
     - Findings are available, or the alert was linked to an existing incident.
   * - **Skipped**
     - Deliberately not investigated. The reason is shown next to the status.

Skip reasons you may see:

* ``daily limit reached`` — the rolling 24-hour budget is spent. The reason shows the count and the limit.
* ``no eligible cluster (external/unknown, no fallback)`` — no **Default agent** is set.
* ``cluster <name> does not support realtime conversations`` — that cluster has no connected agent, or its agent is too old.
* ``auto-investigation disabled for the account`` — **Triage Automatically** was switched off after the alert had already been queued.

Alerts attached to an existing incident by a matching rule are marked triaged without an investigation. See :doc:`/platform/incident-grouping`.

Limitations
-----------

* **Alerts that arrive while Triage Automatically is off are never queued.** They stay ``Not triaged`` in the backlog rather than being marked ``Skipped``. Investigate them manually to run them.
* **Only new alerts are triaged automatically.** A recurrence that reuses an existing alert record does not queue another automatic investigation.
* **The daily limit is a rolling 24-hour window**, not a calendar day, and it counts investigations started rather than investigations that succeeded.
* **The limit applies to automatic runs only.** Manual investigations are never blocked by it.
* **Two of the three setup checklist steps reflect the last 30 days.** *Connect an alert source* and *Investigate your first alert* are ticked from recent activity, not from whether the step was ever done. *Enable Auto Triage* reflects the current setting.
