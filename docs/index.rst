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
   :caption: SRE Agent
   :hidden:

   configuration/holmesgpt/main-features
   configuration/holmesgpt/getting-started
   HolmesGPT Docs <configuration/holmesgpt/holmesgpt-docs>

.. toctree::
   :maxdepth: 4
   :caption: HTTP APIs
   :hidden:

   Overview <configuration/exporting/robusta-pro-features>
   Holmes Chat API <configuration/holmesgpt/holmes-chat-api>
   setup-robusta/alertsui
   configuration/exporting/send-alerts-api
   configuration/exporting/configuration-changes-api
   configuration/exporting/alert-export-api
   configuration/exporting/alert-statistics-api
   configuration/exporting/namespace-resources-api
   configuration/exporting/rbac-api
   configuration/exporting/prometheus-query-api

.. toctree::
   :maxdepth: 4
   :caption: Other Features
   :hidden:

   Send Alerts to Robusta <configuration/index>
   Track Config Changes <track-changes/kubernetes-changes>
   Connect Metrics <configuration/metric-providers>
   Notification Sinks <notification-routing/configuring-sinks>
   Alert Routing <notification-routing/index>
   CRDs Monitoring <setup-robusta/crds>
   Playbooks <playbook-reference/index>

.. toctree::
   :maxdepth: 4
   :caption: Help
   :hidden:

   help

Welcome to Robusta
====================

Robusta is an AI-powered SRE agent that automatically investigates alerts and finds root causes. It is built on `HolmesGPT <https://github.com/robusta-dev/holmesGPT>`_, an open source AI agent that pulls evidence from your existing `data sources <https://holmesgpt.dev/data-sources/?tab=robusta-helm-chart>`_ and uses LLMs to pinpoint what went wrong.

**How it works:**

* **Automatic investigation** — every alert is analyzed with AI-powered root cause analysis
* **Your data sources** — HolmesGPT connects to your existing monitoring, ITSM, and cloud tools to gather evidence
* **Chat with your agent** — tag HolmesGPT in Slack or Teams to investigate issues on demand
* **Centralized control** — the `Robusta Platform <https://home.robusta.dev>`_ gives you a single place to manage your SRE agents, triage alerts, and review investigation timelines

Robusta is available as **open source**, **SaaS**, or **self-hosted**. See :doc:`how-it-works/oss-vs-saas` for details.

Ready to get started?
---------------------

.. button-link:: https://platform.robusta.dev/signup
    :color: primary
    :outline:

    Get Started →
