Open Source vs SaaS
################################

Robusta's Open Source Projects
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Robusta maintains two main open source projects:

**HolmesGPT** — AI-Powered Root Cause Analysis
  `HolmesGPT <https://github.com/robusta-dev/holmesGPT>`_ is Robusta's flagship open source project. It is an AI-powered tool that automatically investigates alerts and surfaces root cause analysis by pulling data from your cluster logs, events, metrics, and other data sources. HolmesGPT uses LLMs to correlate information across sources and provide actionable investigation results. It can be used standalone or as part of the Robusta platform.

**Robusta Classic** — Deterministic Alert Enrichment
  Robusta Classic is the original open source alert engine. It provides deterministic, rule-based alert enrichment using configurable playbooks. When an alert fires, Robusta Classic automatically attaches relevant context — pod logs, resource state, related events, and more — before routing the enriched alert to your notification channels (Slack, Teams, PagerDuty, etc.). Robusta Classic is MIT-licensed with no web UI.

Deployment Options
^^^^^^^^^^^^^^^^^^^

- **Open Source Only**: Run HolmesGPT and/or Robusta Classic on their own. Alerts are enriched and sent directly to Slack, Teams, or other sinks. No web UI.
- **SaaS**: Open source components + Robusta's hosted web UI with :doc:`additional features <../configuration/exporting/robusta-pro-features>` including centralized alert management, multi-cluster visibility, and historical timelines.
- **Self-Hosted**: Open source components + on-premise web UI for organizations that require dedicated infrastructure (enterprise plans).

**Which should I choose?**

Most teams use the **SaaS** option for the :doc:`complete feature set <../configuration/exporting/robusta-pro-features>` without infrastructure overhead. The open source components work well on their own if you only need alert enrichment and routing to external notification channels.

Pricing
^^^^^^^^^^^^
HolmesGPT and Robusta Classic are and always will be free. They are MIT licensed.

The Robusta Platform UI is `free to get started <https://home.robusta.dev/pricing>`_ on our SaaS. If you want to self-host the UI, you'll need an enterprise plan.

Contact support@robusta.dev for questions.

Learn More
^^^^^^^^^^^^
- `HolmesGPT on GitHub <https://github.com/robusta-dev/holmesGPT>`_ - AI-powered root cause analysis
- :doc:`Robusta Pro Features <../configuration/exporting/robusta-pro-features>` - Detailed breakdown of SaaS and enterprise features
- `Pricing Plans <https://home.robusta.dev/pricing>`_ - Compare pricing options and start a free trial
