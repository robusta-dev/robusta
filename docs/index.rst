:hide-toc:

.. toctree::
   :maxdepth: 4
   :caption: Overview
   :hidden:

   self
   how-it-works/architecture
   how-it-works/oss-vs-saas

.. toctree::
   :maxdepth: 4
   :caption: Installation
   :hidden:

   setup-robusta/index

.. toctree::
   :maxdepth: 4
   :caption: HTTP APIs
   :hidden:

   Overview <configuration/exporting/robusta-pro-features>
   Holmes Chat API <configuration/holmesgpt/holmes-chat-api>
   configuration/exporting/send-events-api
   configuration/exporting/alert-export-api
   configuration/exporting/alert-statistics-api
   configuration/exporting/rbac-api

.. toctree::
   :maxdepth: 4
   :caption: GitHub Actions
   :hidden:

   Overview <configuration/github-actions/index>
   HolmesGPT PR Review <configuration/github-actions/holmes-pr-review>

.. toctree::
   :maxdepth: 4
   :caption: Robusta Classic
   :hidden:

   Send Alerts to Robusta <configuration/index>
   Track Config Changes <track-changes/kubernetes-changes>
   Connect Metrics <configuration/metric-providers>
   Notification Sinks <notification-routing/configuring-sinks>
   Alert Routing <notification-routing/index>
   CRDs Monitoring <setup-robusta/crds>
   Playbooks <playbook-reference/index>
   Self-Monitoring <setup-robusta/robusta-runner-metrics>
   Managed Prometheus Alerts <setup-robusta/alertsui>
   Namespace Resources API <configuration/exporting/namespace-resources-api>
   Prometheus Query API <configuration/exporting/prometheus-query-api>

.. toctree::
   :maxdepth: 4
   :caption: Help
   :hidden:

   help

Welcome to Robusta
====================

Robusta is an AI-powered SRE agent that automatically investigates alerts and finds root causes. It is built on `HolmesGPT <https://github.com/robusta-dev/holmesGPT>`_.

**How it works:**

* **Automatic investigation** — every alert is analyzed with AI-powered root cause analysis
* **Your data sources** — HolmesGPT connects to your existing monitoring, ITSM, cloud tools, and MCP servers to gather evidence
* **Chat with your agent** — tag HolmesGPT in Slack or Teams to investigate issues on demand
* **Centralized control** — the `Robusta Platform <https://home.robusta.dev>`_ gives you a single place to manage your SRE agents, triage alerts, and review investigation timelines

Robusta is available as **SaaS**, **self-hosted**, or **open source**. See :doc:`how-it-works/oss-vs-saas` for details.

Ready to get started?
---------------------

.. button-link:: https://platform.robusta.dev/signup
    :color: primary
    :outline:

    Get Started →
