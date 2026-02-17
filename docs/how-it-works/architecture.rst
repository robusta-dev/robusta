Architecture
==================

Robusta uses `HolmesGPT <https://github.com/robusta-dev/holmesGPT>`_, an open source AI agent, to automatically investigate and root-cause Kubernetes alerts. HolmesGPT runs as part of the **in-cluster Agent**, connects to your existing **data sources**, and reports findings through the **Robusta Platform** (SaaS or self-hosted).

.. image:: ../images/architecture-overview.png
   :width: 800
   :align: center

|

Agent (In-Cluster)
^^^^^^^^^^^^^^^^^^^

The Robusta Agent runs inside your Kubernetes cluster. It includes HolmesGPT and is responsible for:

- Fetching data from external `data sources <https://holmesgpt.dev/data-sources/?tab=robusta-helm-chart>`_
- Optional: for customers troubleshooting issues on Kubernetes itself, track new deploys and changes to Kubernetes and query Kubernetes events

The Agent keeps your data secure — it fetches data from your data sources directly, so there is no direct connection from the Robusta Platform to your data sources.

Robusta Platform
^^^^^^^^^^^^^^^^^

The Robusta Platform is a centralized place to control your SRE agents and chat with them. It is available as **SaaS** (hosted by Robusta) or **self-hosted** (for enterprise deployments).

The Platform receives investigation results from HolmesGPT and provides:

- AI-powered root cause analysis results for every alert
- Centralized alert management and triage
- Historical alert analysis and timelines
- HolmesGPT Slack and Teams bot — tag the AI agent like a teammate to investigate issues on demand

Data Sources
^^^^^^^^^^^^^

HolmesGPT integrates with a wide range of `data sources <https://holmesgpt.dev/data-sources/?tab=robusta-helm-chart>`_ in your environment to gather evidence during investigations.

All data source connections are made by the Agent within your environment. The Robusta Platform never connects to your data sources directly.

Security & Networking
^^^^^^^^^^^^^^^^^^^^^

- The Agent runs entirely within your cluster with configurable RBAC permissions
- Data sources are accessed only by the in-cluster Agent, never by the Platform
- SaaS connectivity is outbound-only — no inbound access is required
- All data remains in your cluster unless explicitly sent to configured sinks or the Robusta Platform

Next Steps
^^^^^^^^^^

`Ready to install Robusta? Get started. <https://platform.robusta.dev/signup>`_

.. _Robusta Classic:

----

A Note on Robusta Classic
^^^^^^^^^^^^^^^^^^^^^^^^^^^

You may see references to "Robusta Classic" in parts of this documentation. Robusta Classic is the original open source alert engine that provides deterministic, rule-based enrichment using configurable playbooks — automatically attaching pod logs, resource state, and related events to alerts before routing them to Slack, Teams, PagerDuty, and :doc:`other notification channels <../configuration/configuring-sinks>`.

Robusta Classic can be installed as part of the Agent and runs alongside HolmesGPT, if you like.
