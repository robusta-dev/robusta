Prometheus Query API
====================

.. note::

    This feature is available with the Robusta SaaS platform and self-hosted commercial plans.
    It is not available in the open-source version.

The Prometheus Query API allows you to run PromQL queries against the Prometheus instance
in your connected clusters.

Endpoint
--------

.. code-block::

    POST https://api.robusta.dev/api/accounts/{account_id}/clusters/{cluster_name}/prometheus/query

Path Parameters
---------------

.. list-table::
   :header-rows: 1
   :widths: 20 10 70

   * - Parameter
     - Required
     - Description
   * - account_id
     - Yes
     - Your Robusta account ID (found in generated_values.yaml as ``globalConfig.account_id``)
   * - cluster_name
     - Yes
     - The name of the cluster to query (as shown in the Robusta UI)

Request Body
------------

.. list-table::
   :header-rows: 1
   :widths: 20 10 15 55

   * - Field
     - Required
     - Default
     - Description
   * - promql_query
     - Yes
     -
     - The PromQL query to execute
   * - duration_minutes
     - No
     - 60
     - Time range in minutes (looking back from now)
   * - starts_at
     - No
     -
     - Start time for date range queries (format: ``YYYY-MM-DD HH:MM:SS UTC``)
   * - ends_at
     - No
     -
     - End time for date range queries (format: ``YYYY-MM-DD HH:MM:SS UTC``)
   * - step
     - No
     - 1m
     - Query resolution step (e.g., ``30s``, ``1m``, ``5m``)

.. note::

    You can specify either ``duration_minutes`` OR both ``starts_at`` and ``ends_at``, but not both.
    If neither is specified, ``duration_minutes`` defaults to 60.

Authentication
--------------

Include an API key in the Authorization header:

.. code-block::

    Authorization: Bearer <API_KEY>

The API key must have **Read Metrics** permission. You can generate this token in the platform by navigating to **Settings** -> **API Keys** -> **New API Key**, and creating a key with the "Read Metrics" permission.

Example Request
---------------

Using duration (last 5 minutes):

.. code-block:: bash

    curl -X POST "https://api.robusta.dev/api/accounts/ACCOUNT_ID/clusters/CLUSTER_NAME/prometheus/query" \
      -H "Authorization: Bearer YOUR_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{
        "promql_query": "up",
        "duration_minutes": 5,
        "step": "1m"
      }'

Using date range:

.. code-block:: bash

    curl -X POST "https://api.robusta.dev/api/accounts/ACCOUNT_ID/clusters/CLUSTER_NAME/prometheus/query" \
      -H "Authorization: Bearer YOUR_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{
        "promql_query": "kube_resourcequota{type=\"hard\"}",
        "starts_at": "2024-01-27 10:00:00 UTC",
        "ends_at": "2024-01-27 11:00:00 UTC",
        "step": "1m"
      }'

Replace ``ACCOUNT_ID``, ``CLUSTER_NAME``, and ``YOUR_API_KEY`` with your actual values.

Response Format
---------------

Success response:

.. code-block:: json

    {
      "status": "success",
      "query": "up",
      "data": [
        {
          "metric": {
            "__name__": "up",
            "job": "kubelet",
            "namespace": "kube-system",
            "node": "worker-node-1"
          },
          "timestamps": [1706356800.0, 1706356860.0, 1706356920.0],
          "values": ["1", "1", "1"]
        },
        {
          "metric": {
            "__name__": "up",
            "job": "coredns",
            "namespace": "kube-system",
            "pod": "coredns-7c68b4b998-abc12"
          },
          "timestamps": [1706356800.0, 1706356860.0, 1706356920.0],
          "values": ["1", "1", "1"]
        }
      ]
    }

Response Fields
---------------

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Field
     - Description
   * - status
     - ``success`` or ``error``
   * - query
     - The PromQL query that was executed
   * - data
     - Array of time series results
   * - data[].metric
     - Labels identifying the time series
   * - data[].timestamps
     - Array of Unix timestamps for each data point
   * - data[].values
     - Array of values corresponding to each timestamp

Error Response
--------------

.. code-block:: json

    {
      "status": "error",
      "query": "invalid_query",
      "error": "Error message describing what went wrong"
    }

Common Queries
--------------

Resource quotas (OpenShift/Kubernetes):

.. code-block:: json

    {"promql_query": "kube_resourcequota{type=\"hard\"}"}
    {"promql_query": "kube_resourcequota{type=\"used\"}"}

CPU and memory:

.. code-block:: json

    {"promql_query": "sum(rate(container_cpu_usage_seconds_total[5m])) by (pod, namespace)"}
    {"promql_query": "container_memory_usage_bytes{namespace=\"default\"}"}

Pod status:

.. code-block:: json

    {"promql_query": "kube_pod_status_phase{phase=\"Running\"}"}
    {"promql_query": "kube_pod_container_status_restarts_total"}
