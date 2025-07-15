Robusta Pro Features
====================

.. note::
    These features are available with the Robusta SaaS platform and self-hosted commercial plans. They are not available in the open-source version.

Robusta Pro provides a comprehensive monitoring platform that includes the open-source runner plus a full SaaS UI, advanced integrations, and enterprise APIs. Most users choose Robusta Pro to get the complete Robusta experience with all capabilities and minimal setup.

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

Robusta Pro includes advanced AI-powered investigation capabilities to help you understand and resolve alerts faster.

:doc:`AI Analysis (Holmes GPT) <../holmesgpt/index>`
    Use AI to investigate Kubernetes alerts, analyze logs, and get remediation suggestions automatically.

Additional Pro Features
-----------------------

Beyond the APIs and AI analysis listed above, Robusta Pro includes:

* **Full SaaS UI**: Complete web interface for managing alerts, playbooks, and configuration
* **Managed Prometheus Alerts**: Create and customize Prometheus alerts with templates, without needing to know PromQL
* **Advanced Analytics**: Historical alert data, trends, and reporting dashboards
* **Enterprise Support**: Dedicated support for production deployments

For more details on the differences between open-source and SaaS, see :doc:`Open Source vs SaaS <../../how-it-works/oss-vs-saas>`.

Getting Started
---------------

To access these features:

1. **Robusta SaaS**: `Sign up for free <https://home.robusta.dev/ui/>`_ to get started with the full platform
2. **Self-hosted Commercial**: Contact support@robusta.dev for enterprise plans with self-hosted UI
3. **API Access**: Generate API keys in the Robusta platform under **Settings** → **API Keys**

For detailed API documentation and examples, see :doc:`Alert History Import and Export API <exporting-data>`.