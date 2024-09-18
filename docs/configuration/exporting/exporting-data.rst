.. _alert-history-export:

Exporting Alert History
==========================

Robusta allows you to export alert history data using a simple API call. This feature helps in fetching historical alert details based on specific criteria such as `alert_name`, `account_id`, and time range.

Example Request
^^^^^^^^^^^^^^^^

The following `curl` command demonstrates how to export alert history data for the `CrashLoopBackoff` alert:

.. code-block:: bash

    curl --location 'https://api.robusta.dev/api/alerts?alert_name=CrashLoopBackoff&account_id=ACCOUNT_ID&start_ts=2024-09-02T04%3A02%3A05.032Z&end_ts=2024-09-17T05%3A02%3A05.032Z' \
    --header 'Authorization: Bearer TOKEN_HERE'

In the command, make sure to replace the following placeholders:

- `ACCOUNT_ID`: Your account ID, which can be found in your generated values file.
- `TOKEN_HERE`: Your API token for authentication. You can generate this token in the platform by navigating to **Settings** -> **API Keys** -> **New API Key**, and creating a key with the "Read Alerts" permission.

Response Format
^^^^^^^^^^^^^^^^

The response will contain an array of alert objects with detailed information, as shown in the example below:

.. code-block:: json

    [
        {
            "alert_name": "CrashLoopBackoff",
            "title": "Crashing pod api-gateway-123abc in namespace prod",
            "description": null,
            "source": "kubernetes_api_server",
            "priority": "HIGH",
            "started_at": "2024-09-03T04:09:31.342818+00:00",
            "resolved_at": null,
            "cluster": "prod-cluster-1",
            "namespace": "prod",
            "app": "api-gateway",
            "kind": null,
            "resource_name": "api-gateway-123abc",
            "resource_node": "gke-prod-cluster-1-node-1"
        },
        {
            "alert_name": "CrashLoopBackoff",
            "title": "Crashing pod billing-service-xyz789 in namespace billing",
            "description": null,
            "source": "kubernetes_api_server",
            "priority": "HIGH",
            "started_at": "2024-09-03T04:09:31.496713+00:00",
            "resolved_at": null,
            "cluster": "prod-cluster-2",
            "namespace": "billing",
            "app": "billing-service",
            "kind": null,
            "resource_name": "billing-service-xyz789",
            "resource_node": "gke-prod-cluster-2-node-3"
        }
    ]


Fields in the response include:

- **alert_name**: The name of the alert (e.g., `CrashLoopBackoff`).
- **title**: A short description of the alert event.
- **source**: The source of the alert (e.g., `kubernetes_api_server`).
- **priority**: The priority level of the alert (e.g., `HIGH`).
- **started_at**: The timestamp when the alert was triggered.
- **resolved_at**: The timestamp when the alert was resolved, or `null` if unresolved.
- **cluster**: The cluster where the alert originated.
- **namespace**: The namespace in which the alert occurred.
- **app**: The application associated with the alert.
- **resource_name**: The specific resource that triggered the alert.
- **resource_node**: The node where the resource is located.

Use this API to fetch alert history and integrate it into your monitoring and reporting workflows.
