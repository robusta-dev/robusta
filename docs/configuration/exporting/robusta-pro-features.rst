HTTP APIs
=========

.. note::
    These APIs are available with the Robusta SaaS platform and self-hosted commercial plans. They are not available in the open-source version.

The Robusta Platform exposes REST APIs for programmatic access to alerts, investigations, and platform data.

Holmes Chat API
---------------

:doc:`Holmes Chat API <../holmesgpt/holmes-chat-api>`
    Send questions to HolmesGPT for on-demand root cause analysis via REST.

Data Export and Reporting
-------------------------

* :doc:`Alert Export API <alert-export-api>`: Export historical alert data with filtering by time range, alert name, and account
* :doc:`Alert Reporting API <alert-statistics-api>`: Get aggregated statistics and counts for different alert types
* :doc:`Send Events API <send-events-api>`: Send alerts, incidents, and changes from any monitoring source via a single webhook endpoint
* :doc:`RBAC Configuration API <rbac-api>`: Programmatically manage role-based access control configurations

Getting Started
---------------

To access these APIs:

1. :robusta-url:`Sign up <https://platform.robusta.dev/signup>` for Robusta SaaS or contact support@robusta.dev for self-hosted plans
2. Generate API keys in the Robusta Platform under **Settings** → **API Keys**
