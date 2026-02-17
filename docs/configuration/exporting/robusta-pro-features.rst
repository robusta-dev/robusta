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
* :doc:`Send Alerts API <send-alerts-api>`: Send alerts programmatically from external systems
* :doc:`Configuration Changes API <configuration-changes-api>`: Track configuration changes in your environment
* :doc:`Namespace Resources API <namespace-resources-api>`: Query namespace-level resource information
* :doc:`RBAC Configuration API <rbac-api>`: Programmatically manage role-based access control configurations
* :doc:`Prometheus Query API <prometheus-query-api>`: Run PromQL queries against Prometheus in your connected clusters

Getting Started
---------------

To access these APIs:

1. `Sign up <https://platform.robusta.dev/signup>`_ for Robusta SaaS or contact support@robusta.dev for self-hosted plans
2. Generate API keys in the Robusta Platform under **Settings** → **API Keys**
