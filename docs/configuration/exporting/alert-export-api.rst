Alert Export API
==============================================

.. note::
    This feature is available with the Robusta SaaS platform and self-hosted commercial plans. It is not available in the open-source version.

Use this endpoint to export alert history data. You can filter the results based on specific criteria using query parameters such as ``alert_name``, ``account_id``, and time range.

.. _alert-export-api:

GET https://api.robusta.dev/api/query/alerts
------------------------------------------------------

Query Parameters
^^^^^^^^^^^^^^^^^^^^^^

.. list-table::
   :widths: 20 10 70 10
   :header-rows: 1

   * - Parameter
     - Type
     - Description
     - Required
   * - ``account_id``
     - string
     - The unique account identifier (found in your ``generated_values.yaml`` file).
     - Yes
   * - ``start_ts``
     - string
     - Start timestamp for the alert history query (in ISO 8601 format, e.g., ``2024-09-02T04:02:05.032Z``).
     - Yes
   * - ``end_ts``
     - string
     - End timestamp for the alert history query (in ISO 8601 format, e.g., ``2024-09-17T05:02:05.032Z``).
     - Yes
   * - ``alert_name``
     - string
     - The name of the alert to filter by (e.g., ``CrashLoopBackoff``).
     - Yes

Example Request
^^^^^^^^^^^^^^^^^^^^^^^^^

The following ``curl`` command demonstrates how to export alert history data for the ``CrashLoopBackoff`` alert:

.. code-block:: bash

    curl --location 'https://api.robusta.dev/api/query/alerts?alert_name=CrashLoopBackoff&account_id=ACCOUNT_ID&start_ts=2024-09-02T04%3A02%3A05.032Z&end_ts=2024-09-17T05%3A02%3A05.032Z' \
    --header 'Authorization: Bearer API-KEY'

In the command, make sure to replace the following placeholders:

- ``ACCOUNT_ID``: Your account ID, which can be found in your ``generated_values.yaml`` file.
- ``API-KEY``: Your API Key for authentication. You can generate this token in the platform by navigating to **Settings** -> **API Keys** -> **New API Key**, and creating a key with the "Read Alerts" permission.

Request Headers
^^^^^^^^^^^^^^^^^^^^^^^^^

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - Header
     - Description
   * - ``Authorization``
     - Bearer token for authentication (e.g., ``Bearer TOKEN_HERE``). The token must have "Read Alerts" permission.

Response Format
^^^^^^^^^^^^^^^^^^^^^^^^^^^

The API will return a list of alerts in JSON format. Each alert object contains detailed information about the alert, including the name, priority, source, and related resource information.

Example Response
^^^^^^^^^^^^^^^^^^^^^^^^

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

Response Fields
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. list-table::
   :widths: 25 10 70
   :header-rows: 1

   * - Field
     - Type
     - Description
   * - ``alert_name``
     - string
     - Name of the alert (e.g., ``CrashLoopBackoff``).
   * - ``title``
     - string
     - A brief description of the alert event.
   * - ``source``
     - string
     - Source of the alert (e.g., ``kubernetes_api_server``).
   * - ``priority``
     - string
     - Priority level of the alert (e.g., ``HIGH``).
   * - ``started_at``
     - string
     - Timestamp when the alert was triggered, in ISO 8601 format.
   * - ``resolved_at``
     - string
     - Timestamp when the alert was resolved, or ``null`` if still unresolved.
   * - ``cluster``
     - string
     - The cluster where the alert originated.
   * - ``namespace``
     - string
     - Namespace where the alert occurred.
   * - ``app``
     - string
     - The application that triggered the alert.
   * - ``resource_name``
     - string
     - Name of the resource that caused the alert.
   * - ``resource_node``
     - string
     - The node where the resource is located.

Quick Start Example
^^^^^^^^^^^^^^^^^^^

There is a quick-start `Prometheus report-generator <https://github.com/robusta-dev/prometheus-report-generator>`_ on GitHub that demonstrates how to use the export APIs.