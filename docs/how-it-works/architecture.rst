Architecture
==================

Robusta's architecture is built around three main components: an **in-cluster Agent**, the **Robusta Platform** (SaaS or self-hosted), and integrations with your existing **data sources** and **notification channels**.

.. image:: ../images/architecture-overview.png
   :width: 800
   :align: center

|

Agent (In-Cluster)
^^^^^^^^^^^^^^^^^^^

The Robusta Agent runs inside your Kubernetes cluster. It is responsible for:

- Collecting alerts from Prometheus AlertManager and other sources
- Monitoring Kubernetes resource changes via the API server
- Gathering logs and events from your workloads
- Fetching data from external data sources (Prometheus, Grafana, New Relic, AWS, Jira, ServiceNow, and more)
- Running deterministic alert enrichment playbooks (see :ref:`Robusta Classic <Robusta Classic>` below)
- Running AI-powered root cause analysis with `HolmesGPT <https://github.com/robusta-dev/holmesGPT>`_

The Agent keeps your data secure — it fetches data from your data sources directly, so there is no direct connection from the Robusta Platform to your data sources.

Robusta Platform
^^^^^^^^^^^^^^^^^

The Robusta Platform provides a centralized web UI for managing alerts across clusters. It is available as **SaaS** (hosted by Robusta) or **self-hosted** (for enterprise deployments).

The Platform receives enriched alerts from the Agent and provides:

- Centralized alert management and triage across multiple clusters
- Historical alert analysis and timelines
- AI-powered root cause investigation results from HolmesGPT
- Notification routing to Slack, Microsoft Teams, and other channels
- :doc:`Additional pro features <../configuration/exporting/robusta-pro-features>`

Data Sources
^^^^^^^^^^^^^

The Agent integrates with a wide range of data sources in your environment to gather context for alert investigation:

- **Monitoring**: Prometheus, Grafana, New Relic, AWS CloudWatch, NPAW, Conviva
- **ITSM & Ticketing**: Jira, ServiceNow
- **And more**: The Agent's data source integrations are extensible

All data source connections are made by the Agent within your environment. The Robusta Platform never connects to your data sources directly.

Notification Channels
^^^^^^^^^^^^^^^^^^^^^^

Enriched alerts and investigation results are routed to your preferred notification channels:

- Slack
- Microsoft Teams
- PagerDuty
- And :doc:`many more sinks <../configuration/configuring-sinks>`

Security & Networking
^^^^^^^^^^^^^^^^^^^^^

- The Agent runs entirely within your cluster with configurable RBAC permissions
- Data sources are accessed only by the in-cluster Agent, never by the Platform
- SaaS connectivity is outbound-only — no inbound access is required
- All data remains in your cluster unless explicitly sent to configured sinks or the Robusta Platform

Next Steps
^^^^^^^^^^

:ref:`Ready to install Robusta? Get started. <install>`
