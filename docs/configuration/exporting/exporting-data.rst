Alert History Import and Export API
==============================================

The Robusta SaaS platform exposes several HTTP APIs:

* :ref:`API to export alerts <alert-export-api>`
* :ref:`API to fetch aggregate alert statistics <alert-reporting-api>`
* :ref:`API to send alerts <send-alerts-api>`
* :ref:`API to send configuration changes <send-configuration-changes-api>`

There is an quick-start `Prometheus report-generator <https://github.com/robusta-dev/prometheus-report-generator>`_  on GitHub that demonstrates how to use the export APIs.

.. _alert-export-api:

GET https://api.robusta.dev/api/query/alerts
------------------------------------------------------

Use this endpoint to export alert history data. You can filter the results based on specific criteria using query parameters such as ``alert_name``, ``account_id``, and time range.

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
     - No

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

.. _alert-reporting-api:

GET `https://api.robusta.dev/api/query/report`
------------------------------------------------------------

Use this endpoint to retrieve aggregated alert data, including the count of each type of alert during a specified time range. Filters can be applied using query parameters such as `account_id` and the time range.


Query Parameters
^^^^^^^^^^^^^^^^^^^^

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
     - Start timestamp for the query (in ISO 8601 format, e.g., ``2024-10-27T04:02:05.032Z``).
     - Yes
   * - ``end_ts``
     - string
     - End timestamp for the query (in ISO 8601 format, e.g., ``2024-11-27T05:02:05.032Z``).
     - Yes


Example Request
^^^^^^^^^^^^^^^^^^^^^^^

The following `curl` command demonstrates how to query aggregated alert data for a specified time range:

.. code-block:: bash

    curl --location 'https://api.robusta.dev/api/query/report?account_id=XXXXXX-XXXX_XXXX_XXXXX7&start_ts=2024-10-27T04:02:05.032Z&end_ts=2024-11-27T05:02:05.032Z' \
    --header 'Authorization: Bearer API-KEY'


In the command, make sure to replace the following placeholders:

- `account_id`: Your account ID, which can be found in your `generated_values.yaml` file.
- `API-KEY`: Your API Key for authentication. Generate this token in the platform by navigating to **Settings** -> **API Keys** -> **New API Key**, and creating a key with the "Read Alerts" permission.



Request Headers
^^^^^^^^^^^^^^^^^^^^

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - Header
     - Description
   * - ``Authorization``
     - Bearer token for authentication (e.g., ``Bearer TOKEN_HERE``). The token must have "Read Alerts" permission.

Response Format
^^^^^^^^^^^^^^^^^^^^

The API will return a JSON array of aggregated alerts, with each object containing:

- **`aggregation_key`**: The unique identifier of the alert type (e.g., `KubeJobFailed`).
- **`alert_count`**: The total count of occurrences of this alert type within the specified time range.

Example Response
^^^^^^^^^^^^^^^^^^^^^^^^^
.. code-block:: json

    [
        {"aggregation_key": "KubeJobFailed", "alert_count": 17413},
        {"aggregation_key": "KubePodNotReady", "alert_count": 11893},
        {"aggregation_key": "KubeDeploymentReplicasMismatch", "alert_count": 2410},
        {"aggregation_key": "KubeDeploymentRolloutStuck", "alert_count": 923},
        {"aggregation_key": "KubePodCrashLooping", "alert_count": 921},
        {"aggregation_key": "KubeContainerWaiting", "alert_count": 752},
        {"aggregation_key": "PrometheusRuleFailures", "alert_count": 188},
        {"aggregation_key": "KubeMemoryOvercommit", "alert_count": 187},
        {"aggregation_key": "PrometheusOperatorRejectedResources", "alert_count": 102},
        {"aggregation_key": "KubeletTooManyPods", "alert_count": 94},
        {"aggregation_key": "NodeMemoryHighUtilization", "alert_count": 23},
        {"aggregation_key": "TargetDown", "alert_count": 19},
        {"aggregation_key": "test123", "alert_count": 7},
        {"aggregation_key": "KubeAggregatedAPIDown", "alert_count": 4},
        {"aggregation_key": "KubeAggregatedAPIErrors", "alert_count": 4},
        {"aggregation_key": "KubeMemoryOvercommitTEST2", "alert_count": 1},
        {"aggregation_key": "TestAlert", "alert_count": 1},
        {"aggregation_key": "TestAlert2", "alert_count": 1},
        {"aggregation_key": "dsafd", "alert_count": 1},
        {"aggregation_key": "KubeMemoryOvercommitTEST", "alert_count": 1},
        {"aggregation_key": "vfd", "alert_count": 1}
    ]



Response Fields
^^^^^^^^^^^^^^^^^^^^
.. list-table::
   :widths: 25 10 70
   :header-rows: 1

   * - Field
     - Type
     - Description
   * - ``aggregation_key``
     - string
     - The unique key representing the type of alert (e.g., ``KubeJobFailed``).
   * - ``alert_count``
     - integer
     - The number of times this alert occurred within the specified time range.

Notes
^^^^^^^^^^^^^^^

- Ensure that the `start_ts` and `end_ts` parameters are in ISO 8601 format and are correctly set to cover the desired time range.
- Use the correct `Authorization` token with sufficient permissions to access the alert data.

.. _send-alerts-api:

POST https://api.robusta.dev/api/alerts
----------------------------------------------------
Use this endpoint to send alert data to Robusta. You can send up to 1000 alerts in a single request.

Request Body Schema
^^^^^^^^^^^^^^^^^^^^^^^^

The request body must include the following fields:

.. list-table::
   :widths: 25 10 70 10
   :header-rows: 1

   * - Field
     - Type
     - Description
     - Required
   * - ``account_id``
     - string
     - The unique account identifier.
     - Yes
   * - ``alerts``
     - list
     - A list of alerts to be sent.
     - Yes

Each alert in the ``alerts`` list must follow the specific schema, which includes the following fields:

.. list-table::
   :widths: 20 10 70 10
   :header-rows: 1

   * - Field
     - Type
     - Description
     - Required
   * - ``title``
     - string
     - A short description of the alert.
     - Yes
   * - ``description``
     - string
     - A detailed description of the alert
     - Yes
   * - ``source``
     - string
     - The source of the alert.
     - Yes
   * - ``priority``
     - string (one of: ``critical``, ``high``, ``medium``, ``error``, ``warning``, ``info``, ``low``, ``debug``)
     - The priority level of the alert.
     - Yes
   * - ``aggregation_key``
     - string
     - A key to group alerts that are related.
     - Yes
   * - ``failure``
     - boolean
     - Indicates whether the alert represents a failure (default: ``false``).
     - No
   * - ``starts_at``
     - string (ISO 8601 timestamp)
     - The timestamp when the alert started (optional).
     - No
   * - ``ends_at``
     - string (ISO 8601 timestamp)
     - The timestamp when the alert ended (optional).
     - No
   * - ``labels``
     - dict
     - Extra labels for the alert (optional).
     - No
   * - ``annotations``
     - dict
     - Extra annotations for the alert (optional).
     - No
   * - ``cluster``
     - string
     - Alert's cluster (default: ``external``)
     - No
   * - ``service_key``
     - string
     - A key identifying the service related to the alert (optional).
     - No
   * - ``subject_type``
     - string
     - The type of subject related to the alert (optional).
     - No
   * - ``subject_name``
     - string
     - The name of the subject related to the alert (optional)
     - No
   * - ``subject_namespace``
     - string
     - The namespace of the subject related to the alert (optional).
     - No
   * - ``subject_node``
     - string
     - The node where the subject related to the alert is located (optional).
     - No
   * - ``fingerprint``
     - string
     - A unique identifier for the alert (optional).
     - No

Example Request
^^^^^^^^^^^^^^^

Here is an example of a ``POST`` request to send a list of alerts:

.. code-block:: bash

    curl --location --request POST 'https://api.robusta.dev/api/alerts' \
    --header 'Authorization: Bearer API-KEY' \
    --header 'Content-Type: application/json' \
    --data-raw '{
        "account_id": "ACCOUNT_ID",
        "alerts": [
            {
                "title": "Test Service Down",
                "description": "The Test Service is not responding.",
                "source": "monitoring-system",
                "priority": "high",
                "aggregation_key": "test-service-issues",
                "failure": true,
                "starts_at": "2024-10-07T10:00:00Z",
                "labels": {
                    "environment": "production"
                },
                "annotations": {
                    "env1": "true"
                },
                "cluster": "prod-cluster-1",
                "subject_namespace": "prod",
                "subject_node": "gke-prod-cluster-1-node-1"
            }
        ]
    }'

In this request, replace the following placeholders:

- ``ACCOUNT_ID``: Your account ID, which can be found in your ``generated_values.yaml`` file.
- ``API-KEY``: Your API Key for authentication. You can generate this token by navigating to **Settings** -> **API Keys** -> **New API Key**.

Request Headers
^^^^^^^^^^^^^^^^^^^^

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - Header
     - Description
   * - ``Authorization``
     - Bearer token for authentication (e.g., ``Bearer TOKEN_HERE``). The token must have the necessary permissions to submit alerts.
   * - ``Content-Type``
     - Must be set to ``application/json``.

Response Format
^^^^^^^^^^^^^^^^^^^^

*Success Response*

If the request is successful, the API will return the following response:

.. code-block:: json

    {
        "success": true
    }

- **Status Code**: `200 OK`

*Error Response*

If there is an error in processing the request, the API will return the following format:

.. code-block:: json

    {
        "msg": "Error message here",
        "error_code": 123
    }

- **Status Code**: Varies based on the error (e.g., `400 Bad Request`, `500 Internal Server Error`).

.. _send-configuration-changes-api:

POST https://api.robusta.dev/api/config-changes
--------------------------------------------------------------------

Use this endpoint to send configuration changes to Robusta. You can send up to 1000 configuration changes in a single request.

Request Body Schema
^^^^^^^^^^^^^^^^^^^

The request body must include the following fields:

.. list-table::
   :widths: 25 10 70 10
   :header-rows: 1

   * - Field
     - Type
     - Description
     - Required
   * - ``account_id``
     - string
     - The unique account identifier.
     - Yes
   * - ``config_changes``
     - list
     - A list of configuration changes.
     - Yes

Each configuration change in the ``config_changes`` list must follow the specific schema, which includes the following fields:

.. list-table::
   :widths: 25 10 70 10
   :header-rows: 1

   * - Field
     - Type
     - Description
     - Required
   * - ``title``
     - string
     - A short description of the configuration change.
     - Yes
   * - ``old_config``
     - string
     - The previous configuration value.
     - Yes
   * - ``new_config``
     - string
     - The new configuration value.
     - Yes
   * - ``resource_name``
     - string
     - The name of the resource affected by the configuration change.
     - Yes
   * - ``description``
     - string
     - A detailed description of the configuration change (optional).
     - No
   * - ``source``
     - string
     - The source of the configuration change (default: ``external``).
     - No
   * - ``cluster``
     - string
     - The cluster where the configuration change occurred (default: ``external``).
     - No
   * - ``labels``
     - dict
     - Extra labels for the alert (optional).
     - No
   * - ``annotations``
     - dict
     - Extra annotations for the configuration change (optional).
     - No
   * - ``subject_name``
     - string
     - The name of the subject related to the configuration change (optional).
     - No
   * - ``subject_namespace``
     - string
     - The namespace of the subject related to the configuration change (optional).
     - No
   * - ``subject_node``
     - string
     - The node where the subject related to the configuration change is located (optional).
     - No
   * - ``subject_type``
     - string
     - The type of subject related to the configuration change (optional).
     - No
   * - ``service_key``
     - string
     - A key identifying the service related to the configuration change (optional).
     - No
   * - ``fingerprint``
     - string
     - A unique identifier for the configuration change (optional).
     - No

Example Request
^^^^^^^^^^^^^^^^^^^^

Here is an example of a ``POST`` request to send a list of configuration changes:

.. code-block:: bash

    curl --location --request POST 'https://api.robusta.dev/api/config-changes' \
    --header 'Authorization: Bearer API-KEY' \
    --header 'Content-Type: application/json' \
    --data-raw '{
        "account_id": "ACCOUNT_ID",
        "config_changes": [
            {
                "title": "Updated test-service deployment",
                "old_config": "apiVersion: apps/v1\nkind: Deployment\n....",
                "new_config": "apiVersion: apps/v1...",
                "resource_name": "test sercvice",
                "description": "Changed deployemnt",
                "source": "test-service",
                "cluster": "prod-cluster-1",
                "labels": {
                    "environment": "production"
                },
                "annotations": {
                    "env1": "true"
                },
                "subject_namespace": "prod",
                "subject_node": "gke-prod-cluster-1-node-1"
            }
        ]
    }'

In this request, replace the following placeholders:

- ``ACCOUNT_ID``: Your account ID, which can be found in your ``generated_values.yaml`` file.
- ``API-KEY``: Your API Key for authentication. You can generate this token by navigating to **Settings** -> **API Keys** -> **New API Key**.

Request Headers
^^^^^^^^^^^^^^^^^^^^

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - Header
     - Description
   * - ``Authorization``
     - Bearer token for authentication (e.g., ``Bearer TOKEN_HERE``). The token must have the necessary permissions to submit configuration changes.
   * - ``Content-Type``
     - Must be set to ``application/json``.

Response Format
^^^^^^^^^^^^^^^^^^^^

*Success Response*

If the request is successful, the API will return the following response:

.. code-block:: json

    {
        "success": true
    }

- **Status Code**: `200 OK`

*Error Response*

If there is an error in processing the request, the API will return the following format:

.. code-block:: json

    {
        "msg": "Error message here",
        "error_code": 123
    }

- **Status Code**: Varies based on the error (e.g., `400 Bad Request`, `500 Internal Server Error`).
