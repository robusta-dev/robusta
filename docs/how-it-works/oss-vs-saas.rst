Open Source vs SaaS
################################

HolmesGPT (Open Source)
^^^^^^^^^^^^^^^^^^^^^^^^

At the core of Robusta is `HolmesGPT <https://github.com/robusta-dev/holmesGPT>`_ — an open source, AI-powered agent that automatically investigates Kubernetes alerts and identifies root causes.

HolmesGPT pulls data from your cluster logs, events, metrics, and external data sources like Prometheus, Grafana, New Relic, and more. It uses LLMs to correlate evidence across sources and produce actionable root cause analysis — turning noisy alerts into clear answers.

HolmesGPT is MIT-licensed and can be used standalone or as part of the Robusta platform.

Deployment Options
^^^^^^^^^^^^^^^^^^^

- **Open Source Only**: Run HolmesGPT on its own. Investigation results are sent directly to Slack, Teams, or other sinks. No web UI.
- **SaaS**: HolmesGPT + Robusta's hosted web UI with :doc:`additional features <../configuration/exporting/robusta-pro-features>` including centralized alert management, multi-cluster visibility, and historical timelines.
- **Self-Hosted**: HolmesGPT + on-premise web UI for organizations that require dedicated infrastructure (enterprise plans).

**Which should I choose?**

Most teams use the **SaaS** option for the :doc:`complete feature set <../configuration/exporting/robusta-pro-features>` without infrastructure overhead. The open source HolmesGPT works well on its own if you only need AI-powered investigation and routing to external notification channels.

Pricing
^^^^^^^^^^^^
HolmesGPT is and always will be free. It is MIT licensed.

The Robusta Platform UI is `free to get started <https://home.robusta.dev/pricing>`_ on our SaaS. If you want to self-host the UI, you'll need an enterprise plan.

Contact support@robusta.dev for questions.

Learn More
^^^^^^^^^^^^
- `HolmesGPT on GitHub <https://github.com/robusta-dev/holmesGPT>`_ - AI-powered root cause analysis for Kubernetes
- :doc:`Robusta Pro Features <../configuration/exporting/robusta-pro-features>` - Detailed breakdown of SaaS and enterprise features
- `Pricing Plans <https://home.robusta.dev/pricing>`_ - Compare pricing options and start a free trial
