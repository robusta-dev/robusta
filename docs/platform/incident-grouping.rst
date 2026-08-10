.. _incident-grouping:

Incident Grouping
==================

Robusta groups related alerts and investigations into **incidents**, so one underlying problem appears as a single item instead of many.

Grouping is **AI-based**. Holmes compares a new finding against the incidents that are already open and decides whether it shares the same *root cause* — not merely the same alert name, resource, or symptom. Two different alerts caused by the same failing dependency belong to one incident; the same alert firing twice for two unrelated reasons belongs to two.

Open **Alerts → Incidents** to browse them.

What an Incident Contains
-------------------------

Each incident gets a stable ``INC-###`` identifier and holds:

* **Title** and **summary** of the underlying problem.
* **Likely cause** and **suggested fix**.
* **Priority**.
* **Workloads** and **environments** affected — these accumulate as more findings attach.
* The alerts and investigation runs attached to it. An attached run records why it was attached; an attached alert shows a reason only when an auto-attach rule matched it, in which case it is tagged **Rule-attached**.

When an attaching finding adds something new — a further detail about the root cause, or a workload or environment the incident did not already cover — Holmes updates the summary so it still describes the whole problem. A routine recurrence that adds nothing new leaves the summary as it is; only the attached findings and the affected workload and environment lists grow.

Enabling Incident Grouping
--------------------------

Grouping is off by default and is enabled separately for each source of findings:

* **Alert triage** — **Alerts → Triage → Settings → Triage Settings → Create incidents from investigations**. The **Settings** button opens the **Pipeline Settings** dialog.
* **Triggered workflows** — the **Create incidents from this workflow** switch on each workflow. See :doc:`/platform/triggered-workflows`.

Enabling it for one does not enable it for the other.

Recurrences and Episodes
------------------------

An incident tracks **one problem, not a workload's whole history**. Holmes opens a new incident rather than reusing an old one when:

* the previous incident was already resolved or the system recovered,
* days passed with no occurrences, or
* the investigation points at a different cause.

So an OOMKill on Monday and an OOMKill on Wednesday on the same deployment may legitimately be two incidents if the causes differ. When Holmes is unsure, it opens a new incident — a wrong merge hides a real problem, while duplicates are easy to merge afterwards.

Auto-Attaching Recurring Incidents
----------------------------------

When Holmes creates an incident it can also write a **matcher** — a simple rule describing which future events belong to that incident — so the same known failure is not investigated repeatedly. A later event matching the rule is attached immediately, with no AI investigation and without consuming your daily investigation budget.

Matchers are opt-in per feature, under **Settings → Feature Flags**:

* **AI Triage → Auto-attach recurring incidents** — for alert triage.
* **Triggered Workflows → Auto-attach recurring incidents** — for triggered workflows.

.. note::

    These are two separate flags with the same label, and they do not gate identically:

    * **Triggered workflows** — rule-based attaching also requires **Create incidents from this workflow** on the workflow itself.
    * **Alert triage** — the feature flag alone is enough. Matching runs before any other check, so alerts keep attaching to existing incidents even with **Create incidents from investigations** turned off. With that switch off Holmes no longer writes new matchers from alert investigations, but matchers already stored on open incidents still match.

Matchers are deliberately conservative:

* A matcher is a fixed set of conditions on the event's fields — never executable code.
* Holmes is instructed to match on stable identity (alert name, namespace, workload, exact error signature) and never on per-firing values such as pod hashes, timestamps, or trace IDs.
* If a matcher does not fit an event, or if **more than one** incident matches, the event falls through to a normal AI investigation instead of guessing.
* Only the 50 most recently updated open incidents are scanned. Attaching a finding refreshes an incident's position, so actively recurring incidents stay in the window, but long-dormant open incidents can drop out of it.

Alerts attached this way are marked as rule-attached. Clicking **Investigate** on such an alert also attaches it instantly rather than starting an investigation — that is expected.

.. warning::

    A matcher that is too broad will silently pull unrelated events into the wrong incident, and there is no re-evaluation to undo it.

    Where you can see the rule depends on the incident's source. On triggered-workflow incidents it is shown read-only in the **Auto-attach rule** panel on the incident page. On alert incidents it is not displayed; the only view of it is the rule named in each **Rule-attached** alert's tag.

    A matcher cannot be edited or deleted from the UI. To stop a bad one, close the incident — only open incidents are scanned — or turn off the corresponding **Auto-attach recurring incidents** flag.

At Scale
--------

For AI grouping, Holmes is shown the most recently updated open incidents — up to 40, trimmed further to fit the prompt — with incidents from the same cluster listed first. When more exist, it is told to search the rest before concluding that a finding is new. Keeping resolved incidents closed keeps grouping accurate.

Other Kinds of Grouping
-----------------------

"Grouping" means different things at different layers of Robusta. They coexist and solve different problems:

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - Feature
     - What it does
   * - **Incident grouping** (this page)
     - AI decides that findings share a root cause and merges them into a persistent ``INC-###`` incident with a summary, cause, and fix. Runs in the Robusta platform and works with any alert source.
   * - :doc:`Notification grouping </notification-routing/notification-grouping>`
     - Threads Slack notifications together so a channel is not flooded. Runs in the in-cluster Robusta runner, is configured in Helm values, groups by fixed fields such as ``namespace`` or ``severity``, and does not analyze causes.

Notification grouping is a delivery-layer feature and is not replaced by incident grouping; the two can be used together.

Alerts that have not been linked to an incident may still be collapsed in the alert list as duplicates of one another. That duplicate detection is also AI-based — it is the first step of each investigation — but it only compares against a small set of recently investigated alerts, and it produces a pointer to a group leader rather than a persistent incident with a summary, cause, and fix.
