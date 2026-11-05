HTTP APIs
=========

.. note::
    These APIs are available with the Robusta SaaS platform and self-hosted commercial plans. They are not available in the open-source version.

The Robusta Platform exposes REST APIs for programmatic access to alerts, investigations, and platform data. Every request is authenticated with an :ref:`API key <http-api-key-permissions>`, scoped to one or more of the permissions below.

Robusta AI
----------

* :doc:`Holmes Chat API <../holmesgpt/holmes-chat-api>`: Send questions to HolmesGPT for on-demand root cause analysis via REST, including a streaming (SSE) mode
* :doc:`Platform MCP API <platform-mcp-api>`: Connect an external MCP client (Claude Code, Claude Desktop, or your own agent) to run Robusta's cross-cluster investigation tools
* :doc:`LLM Models API <llm-models-api>`: List the Robusta-hosted LLM models available to your account and its default model

Data Export and Reporting
--------------------------

* :doc:`Alert Export API <alert-export-api>`: Export historical alert data with filtering by time range, alert name, and account
* :doc:`Alert Reporting API <alert-statistics-api>`: Get aggregated statistics and counts for different alert types
* :doc:`Send Events API <send-events-api>`: Send alerts, incidents, and changes from any monitoring source via a single webhook endpoint

RBAC
----

* :doc:`RBAC Configuration API <rbac-api>`: Programmatically manage role-based access control configurations

.. _http-api-key-permissions:

API Key Permissions
--------------------

Every API key is scoped by a set of resource/action pairs, chosen when the key is created under **Settings** → **API Keys** → **New API Key**. The table below lists every permission and the HTTP APIs it unlocks.

.. list-table::
   :widths: 15 15 45 25
   :header-rows: 1

   * - Resource
     - Action
     - Grants access to
     - Docs
   * - Alerts
     - Read
     - Export alert history and aggregated alert statistics
     - :doc:`Alert Export API <alert-export-api>`, :doc:`Alert Reporting API <alert-statistics-api>`
   * - Alerts
     - Write
     - Ingest alerts, incidents, and config changes into Robusta
     - :doc:`Send Events API <send-events-api>`, :doc:`Send Alerts API (legacy) <send-alerts-api>`, :doc:`Configuration Changes API (legacy) <configuration-changes-api>`
   * - Robusta AI
     - Write
     - Ask HolmesGPT to investigate, run MCP tools against your clusters, and list available LLM models
     - :doc:`Holmes Chat API <../holmesgpt/holmes-chat-api>`, :doc:`Platform MCP API <platform-mcp-api>`, :doc:`LLM Models API <llm-models-api>`
   * - RBAC
     - Read / Write
     - Read or replace the account's role-based access control configuration
     - :doc:`RBAC Configuration API <rbac-api>`
   * - Agents
     - Read
     - Read active Kubernetes resource counts for a namespace, as shown in the UI's Namespaces tab
     - :doc:`Namespace Resources API <namespace-resources-api>` (Robusta Classic)
   * - KRR
     - Read
     - Retrieve KRR resource-sizing recommendations for a cluster
     - :ref:`KRR API <krr-api>` (Robusta Classic)
   * - Metrics
     - Read
     - Run a PromQL query against a connected cluster's Prometheus
     - :doc:`Prometheus Query API <prometheus-query-api>` (Robusta Classic)

Getting Started
---------------

To access these APIs:

1. :robusta-url:`Sign up <https://platform.robusta.dev/signup>` for Robusta SaaS or contact support@robusta.dev for self-hosted plans
2. Generate API keys in the Robusta Platform under **Settings** → **API Keys**
