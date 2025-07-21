Robusta Pro Features
====================

.. note::
    These features are available with the Robusta SaaS platform and self-hosted commercial plans. They are not available in the open-source version.

Robusta Pro adds a web UI, additional integrations, and enterprise APIs to the open-source engine. Available as SaaS (we handle hosting) or self-hosted on-premise.

Custom Alert Ingestion
-----------------------

Send alerts to Robusta from any monitoring system using HTTP webhooks.

:doc:`Custom Webhooks <custom-webhooks>`
    Send alerts from any system that supports HTTP webhooks, including custom monitoring solutions.

:doc:`Nagios Integration <../alertmanager-integration/nagios>`
    Forward alerts from Nagios to Robusta for enrichment and automation.

:doc:`SolarWinds Integration <../alertmanager-integration/solarwinds>`
    Configure SolarWinds to send alert webhooks directly to Robusta.

Data Export and Reporting APIs
-------------------------------

Export alert history and generate reports using Robusta's REST APIs.

:doc:`Alert History Import and Export API <exporting-data>`
    Comprehensive API for exporting alert history, generating reports, and sending custom alerts programmatically.

Features include:

* **Alert Export API**: Export historical alert data with filtering by time range, alert name, and account
* **Alert Reporting API**: Get aggregated statistics and counts for different alert types
* **Custom Alert API**: Send alerts programmatically from external systems
* **Configuration Changes API**: Track configuration changes in your environment

AI Analysis
-----------

Optional AI-powered alert investigation using HolmesGPT.

:doc:`AI Analysis (HolmesGPT) <../holmesgpt/index>`
    Automatically analyze Kubernetes alerts, logs, and metrics. Get potential root causes and remediation suggestions.

Additional Pro Features
-----------------------

Additional capabilities in Robusta Pro:

* **Web UI**: Manage alerts, playbooks, and configuration through a browser interface
* **Alert Templates**: Create Prometheus alerts without writing PromQL
* **Historical Data**: Query alert history and trends
* **Enterprise Support**: Production support and SLA options

For more details on the differences between open-source and SaaS, see :doc:`Open Source vs SaaS <../../how-it-works/oss-vs-saas>`.

Getting Started
---------------

To access these features:

1. **Robusta SaaS**: `Sign up for free <https://home.robusta.dev/ui/>`_ to get started with the full platform
2. **Self-hosted Commercial**: Contact support@robusta.dev for enterprise plans with self-hosted UI
3. **API Access**: Generate API keys in the Robusta platform under **Settings** → **API Keys**

For detailed API documentation and examples, see :doc:`Alert History Import and Export API <exporting-data>`.