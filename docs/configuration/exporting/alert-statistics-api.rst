Alert Statistics API
==============================================

.. note::
    This feature is available with the Robusta SaaS platform and self-hosted commercial plans. It is not available in the open-source version.

Use this endpoint to retrieve aggregated alert data, including the count of each type of alert during a specified time range. Filters can be applied using query parameters such as `account_id` and the time range.

.. _alert-reporting-api:

GET https://api.robusta.dev/api/query/report
------------------------------------------------------------

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

Quick Start Example
^^^^^^^^^^^^^^^^^^^

There is a quick-start `Prometheus report-generator <https://github.com/robusta-dev/prometheus-report-generator>`_ on GitHub that demonstrates how to use the export APIs.