Deployment Options
################################

Robusta is delivered through the **Robusta Platform** — a centralized place to control your SRE agents, triage alerts, and review investigation timelines. The Platform is available as **SaaS** (hosted by Robusta) or **Self-Hosted** (for organizations with dedicated infrastructure requirements).

SaaS (Hosted)
^^^^^^^^^^^^^^

The hosted Platform runs in Robusta's infrastructure. You install the in-cluster Agent, sign up at `platform.robusta.dev <https://platform.robusta.dev/signup>`_, and your alerts and investigations stream into the hosted UI.

Most teams use SaaS — it's the fastest path to the complete feature set.

Self-Hosted
^^^^^^^^^^^^

The same Platform, deployed inside your own infrastructure. Intended for organizations that require dedicated infrastructure (regulatory, data residency, or air-gapped requirements).

Self-hosted deployments are available on enterprise plans — contact support@robusta.dev.

Pricing
^^^^^^^^^^^^

The SaaS Platform is `free to get started <https://home.robusta.dev/pricing>`_, with paid tiers for larger teams and advanced features. Self-hosted deployments require an enterprise plan.

Open Source
^^^^^^^^^^^^

`HolmesGPT <https://github.com/robusta-dev/holmesGPT>`_ — the SRE agent at the core of Robusta — is MIT-licensed and a CNCF sandbox project. Standalone HolmesGPT is CLI- and HTTP-API-only. See `holmesgpt.dev <https://holmesgpt.dev/>`_ for standalone usage.

The Robusta Platform (SaaS or Self-Hosted) adds on top:

- A web interface for alert triage and investigation history
- HolmesGPT bots for Slack and Microsoft Teams
- Automatic alert triage and grouping

Robusta Classic
^^^^^^^^^^^^^^^^

Before HolmesGPT, Robusta's open source engine focused on rule-based automation — enriching alerts with extra context (logs, pod status, resource graphs) and routing them to Slack, Teams, and other sinks using configurable playbooks. This is sometimes referred to as **Robusta Classic**.

If you are running Robusta Classic, upgrading to HolmesGPT is a configuration change — no migration required.
