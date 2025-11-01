Overview
========

.. note::
    These features are available with the Robusta SaaS platform and self-hosted commercial plans. They are not available in the open-source version.

Robusta Pro adds a web UI, additional integrations, and enterprise APIs to the open-source engine. Available as SaaS (we handle hosting) or self-hosted on-premise.

AI Analysis
-----------

Automatically investigate and resolve issues with AI-powered analysis.

:doc:`AI Analysis (HolmesGPT) <../holmesgpt/main-features>`
    Automatically analyze Kubernetes alerts, logs, and metrics. Get potential root causes and remediation suggestions.

Custom Alert Ingestion
-----------------------

Send alerts to Robusta from any monitoring system using HTTP webhooks.

:doc:`Custom Webhooks <custom-webhooks>`
    Send alerts from any system that supports HTTP webhooks, including custom monitoring solutions.

:doc:`New Relic Integration <../alertmanager-integration/newrelic>`
    Forward alerts from New Relic to Robusta via webhooks.

:doc:`LaunchDarkly Integration <../alertmanager-integration/launchdarkly>`
    Forward feature flag changes from LaunchDarkly to Robusta via webhooks.

:doc:`SolarWinds Integration <../alertmanager-integration/solarwinds>`
    Configure SolarWinds to send alert webhooks directly to Robusta.

:doc:`Nagios Integration <../alertmanager-integration/nagios>`
    Forward alerts from Nagios to Robusta for enrichment and automation.

Data Export and Reporting APIs
-------------------------------

Export alert history and generate reports using Robusta's REST APIs.

**Robusta API Reference**
    Comprehensive APIs for exporting alert history, generating reports, and sending custom alerts programmatically.

Features include:

* :doc:`Alert Export API <alert-export-api>`: Export historical alert data with filtering by time range, alert name, and account
* :doc:`Alert Reporting API <alert-statistics-api>`: Get aggregated statistics and counts for different alert types
* :doc:`Send Alerts API <send-alerts-api>`: Send alerts programmatically from external systems or via integrations
* :doc:`Configuration Changes API <configuration-changes-api>`: Track configuration changes in your environment
* :doc:`RBAC Configuration API <rbac-api>`: Programmatically manage role-based access control configurations

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

1. **Robusta SaaS**: `Sign up for free <https://platform.robusta.dev/signup>`_ to get started with the full platform
2. **Self-hosted Commercial**: Contact support@robusta.dev for enterprise plans with self-hosted UI
3. **API Access**: Generate API keys in the Robusta platform under **Settings** → **API Keys**

For detailed API documentation and examples, see the individual API references listed above.