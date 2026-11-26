Cost Savings (KRR)
************************************************************

`KRR <https://github.com/robusta-dev/krr>`_ is a CLI tool that optimizes resource allocation in Kubernetes clusters.
It gathers pod usage data from Prometheus and recommends requests and limits for CPU and memory, reducing costs and improving performance.

Robusta can run KRR scans on a :ref:`schedule <Scheduled>` using playbooks. Because KRR is so popular, it has dedicated documentation here. You can:

1. Send weekly scan reports to Slack or other sinks via Robusta OSS (disabled by default, configure below)
2. View scans from all your clusters in the Robusta UI (enabled by default for UI users)


.. _krr-cronjob:

Weekly KRR Scan CronJob
===========================================

The Helm chart creates a ``CronJob`` named ``<release>-krr`` that runs the weekly KRR scan and sends the result
to the Robusta UI. It replaces the ``WeeklyKRRScan`` playbook, so the runner does not create the scan Job
or a Secret for it. It runs with the runner service account, and uses the Prometheus settings from
``globalConfig`` and the runner's ``additional_env_vars`` and ``additional_env_froms``.

Existing KRR settings keep working: ``krr_args``, ``krr_job_spec``, ``max_workers``, ``krr_verbose``, ``strategy``,
``timeout`` and ``custom_annotations`` under ``globalConfig``, and the ``KRR_IMAGE_OVERRIDE``, ``KRR_MEMORY_REQUEST``,
``KRR_MEMORY_LIMIT``, ``KRR_STRATEGY`` and ``KRR_PUBLISH_URL`` runner environment variables. A value under
``runner.krrCronJob`` takes precedence:

.. code-block:: yaml

    runner:
      krrCronJob:
        enabled: true
        schedule: "0 12 * * 1"   # every Monday at 12:00
        timeout: ~               # seconds. globalConfig.timeout, then 3600
        image: ~                 # KRR_IMAGE_OVERRIDE, then image.registry/krr
        strategy: ~              # KRR_STRATEGY, globalConfig.strategy, then simple
        krrArgs: ""              # globalConfig.krr_args
        maxWorkers: ~            # globalConfig.max_workers, then 3
        verbose: false           # or globalConfig.krr_verbose
        memoryRequest: ~         # KRR_MEMORY_REQUEST, then 2Gi
        memoryLimit: ~           # KRR_MEMORY_LIMIT, then 2Gi
        jobSpec: {}              # tolerations, nodeSelector, affinity...
        annotations: {}          # added to globalConfig.custom_annotations
        prometheusAuthSecret:    # a Secret holding the Prometheus Authorization header
          name: ""
          key: ""

A ``krr_scan`` action in ``customPlaybooks`` does not run while the CronJob is enabled, and the runner logs an error instead. Remove it and set the frequency with ``runner.krrCronJob.schedule``.

The CronJob is not created without a Robusta UI sink, or when ``WeeklyKRRScan`` is listed in ``disabledPlaybooks``.

To run a scan now, and to check previous runs (replace ``robusta`` with your release name and namespace):

.. code-block:: bash

    kubectl create job --from=cronjob/robusta-krr krr-manual -n robusta
    kubectl get jobs -l app=krr.robusta.dev -n robusta

Limitations of the CronJob:

- **Azure Managed Prometheus**: authentication with ``AZURE_CLIENT_ID``/``AZURE_TENANT_ID`` and ``AZURE_CLIENT_SECRET`` or ``AZURE_USE_MANAGED_ID`` is not supported. Provide a token with ``prometheusAuthSecret``
- **Log mode**: ``KRR_PUSH_SCAN=false`` is not supported
- **Failed runs**: a run that is killed (out of memory, timeout) is not reported to the Robusta UI. KRR still reports its own input and Prometheus errors. Check the Jobs with the command above
- **Scan now**: the "scan now" button in the Robusta UI is not supported. Run a scan with the command above

Sending Weekly KRR Scan Reports to Slack
===========================================
With or without the UI, you can configure additional scans on a :ref:`schedule <Scheduled>`. The results can be sent as a PDF to Slack. Follow the steps below to set it up

1. Install Robusta with Helm to your cluster and configure Slack sink.
2. Create your KRR slack playbook by adding the following to ``generated_values.yaml``:

.. code-block:: yaml

    # Runs a weekly krr scan on the namespace devs-namespace and sends it to the configured slack channel
    customPlaybooks:
    - triggers:
      - on_schedule:
          fixed_delay_repeat:
            repeat: -1 # number of times to run or -1 to run forever
            seconds_delay: 604800 # 1 week
      actions:
      - krr_scan:
          args: "--namespace devs-namespace" ## KRR args here
      sinks:
          - "main_slack_sink" # slack sink you want to send the report to here

   Scheduled ``krr_scan`` playbooks need ``runner.krrCronJob.enabled: false``, see :ref:`krr-cronjob`.

3. Do a Helm upgrade to apply the new values: ``helm upgrade robusta robusta/robusta --values=generated_values.yaml --set clusterName=<YOUR_CLUSTER_NAME>``

.. grid:: 1 1 1 1

    .. grid-item::

        .. md-tab-set::

            .. md-tab-item:: Slack

                .. image:: /images/krr_slack_example.png
                    :width: 1000px

            .. md-tab-item:: Robusta UI

                .. image:: /images/krr_example.png
                    :width: 1000px

Taints, Tolerations and NodeSelectors
============================================

To run KRR on an ARM cluster or on specific nodes you can set custom tolerations or a nodeSelector in your ``generated_values.yaml`` file as follows:

.. code-block:: yaml
    :name: cb-krr-set-custom-taints

    globalConfig:
      krr_job_spec:
        tolerations:
        - key: "key1"
          operator: "Exists"
          effect: "NoSchedule"
        nodeSelector:
          nodeName: "your-selector"

Customizing Efficiency Recommendations in the Robusta UI
====================================================================================
You can tweak KRR's recommendation algorithm to suit your environment using the ``krr_args`` setting in Robusta's Helm chart.

Add the following config to the top of your ``generated_values.yaml`` with your custom values. KRR will use these values every time it sends data to the Robusta UI or other destinations.

If you are having performance issues, specifically with Prometheus using a lot of memory, reduce ``max_workers`` to reduce memory usage. KRR uses 3 workers by default.

.. code-block:: yaml

    globalConfig:
      krr_args: "--cpu-min 15 --mem-min 200 --cpu_percentile 90 --memory_buffer_percentage 25"
      max_workers: 2

Enabling HPA Recommendations in the Robusta UI
------------------------------------------------------------
To enable Horizontal Pod Autoscaler (HPA) recommendations in the Robusta UI, add the following to your ``generated_values.yaml`` file:

.. code-block:: yaml

    globalConfig:
      krr_args: "--allow-hpa"

Common KRR Settings
---------------------

.. list-table::
   :widths: 25 10 40 25
   :header-rows: 1

   * - ``Argument``
     - Type
     - Used for
     - Default value
   * - ``--allow-hpa``
     - BOOLEAN
     - Get recommendations for applications with `HPA <https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/>`_
     - FALSE
   * - ``--cpu-min``
     - INTEGER
     - Sets the minimum recommended CPU value in millicores.
     - 10
   * - ``--mem-min``
     - INTEGER
     - Sets the minimum recommended memory value in MB.
     - 100
   * - ``--history_duration``
     - TEXT
     - The duration of the history data to use (in hours).
     - 336
   * - ``--timeframe_duration``
     - TEXT
     - The step for the history data (in minutes).
     - 1.25
   * - ``--cpu_percentile``
     - TEXT
     - The percentile to use for the CPU recommendation.
     - 99
   * - ``--memory_buffer_percentage``
     - TEXT
     - The percentage of added buffer to the peak memory usage for memory recommendation.
     - 15
   * - ``--points_required``
     - TEXT
     - The number of data points required to make a recommendation for a resource.
     - 100
   * - ``--use_oomkill_data``
     - BOOL
     - Whether to bump the memory when OOMKills are detected.
     - FALSE

Configuring KRR Job Memory Requests and Limits
======================================================

To prevent the KRR job from OOMKill (Out of Memory), you can configure the memory requests and limits by adding the following environment variables to your ``generated_values.yaml`` file:

.. code-block:: yaml

    runner:
      additional_env_vars:
      - name: KRR_MEMORY_REQUEST
        value: "3Gi"
      - name: KRR_MEMORY_LIMIT
        value: "3Gi"

By default, the memory request and limit are set to ``2Gi``. Modify these values according to your requirements.

For the weekly scan :ref:`CronJob <krr-cronjob>`, ``KRR_MEMORY_REQUEST``, ``KRR_MEMORY_LIMIT`` and ``KRR_IMAGE_OVERRIDE`` must be set with a literal ``value`` as above. Values from ``valueFrom`` or ``additional_env_froms`` are not used; set ``runner.krrCronJob.memoryRequest``, ``memoryLimit`` or ``image`` instead.

Enable KRR security context
======================================

To enable KRR security context, add the following to your ``generated_values.yaml`` file:

.. code-block:: yaml

    runner:
      setKRRSecurityContext: true



.. _krr-api:

KRR API
======================================

You can retrieve KRR recommendations programmatically using the Robusta API. This allows you to integrate resource recommendations into your own tools and workflows.


Authentication
---------------------

The KRR API requires authentication via API key.

To create your key, on the ``Robusta Platform``, go to the ``settings`` page, and choose the ``API keys`` tab.

Click ``New API Key``. Choose a name for your key, and check the ``KRR Read`` capability.

.. image:: /images/krr-api-key.png
    :width: 500px

GET /api/krr/recommendations
----------------------------------------------------

Retrieves KRR resource recommendations for a specific cluster and namespace.

**Query Parameters**

.. list-table::
   :widths: 20 15 40 15
   :header-rows: 1

   * - Parameter
     - Type
     - Description
     - Required
   * - ``account_id``
     - STRING
     - The account ID associated with the API key
     - Yes
   * - ``cluster_id``
     - STRING
     - The cluster ID to get recommendations for
     - Yes
   * - ``namespace``
     - STRING
     - The namespace to filter recommendations (optional)
     - No

**Request Headers**

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - Header
     - Value
   * - ``Authorization``
     - ``Bearer <your-api-key>``
   * - ``Content-Type``
     - ``application/json``

**Example Request**

.. robusta-code:: bash

    curl -X GET "https://api.robusta.dev/api/krr/recommendations?account_id=YOUR_ACCOUNT_ID&cluster_id=my-cluster&namespace=default" \
      -H "Authorization: Bearer YOUR_API_KEY" \
      -H "Content-Type: application/json"

**Success Response (200 OK)**

.. code-block:: json

    {
      "cluster_id": "my-cluster",
      "scan_id": "12345-67890-abcde",
      "scan_date": "2024-01-07T12:00:00Z",
      "scan_state": "success",
      "results": [
        {
          "cluster_id": "my-cluster",
          "namespace": "default",
          "name": "nginx-deployment",
          "kind": "Deployment",
          "container": "nginx",
          "priority": "MEDIUM",
          "current_cpu_request": 100,
          "recommended_cpu_request": 50,
          "current_cpu_limit": 500,
          "recommended_cpu_limit": 200,
          "current_memory_request": 134217728,
          "recommended_memory_request": 67108864,
          "current_memory_limit": 536870912,
          "recommended_memory_limit": 268435456,
          "pods_count": 3
        }
      ]
    }

**Response Fields**

.. list-table::
   :widths: 30 15 55
   :header-rows: 1

   * - Field
     - Type
     - Description
   * - ``cluster_id``
     - STRING
     - The cluster ID for which recommendations were generated
   * - ``scan_id``
     - STRING
     - Unique identifier for this KRR scan
   * - ``scan_date``
     - STRING
     - Timestamp when the scan was completed (ISO 8601 format)
   * - ``scan_state``
     - STRING
     - State of the scan (e.g., "success")
   * - ``results``
     - ARRAY
     - Array of KRR recommendations for workloads
   * - ``results[].cluster_id``
     - STRING
     - Cluster ID of the workload
   * - ``results[].namespace``
     - STRING
     - Namespace of the workload
   * - ``results[].name``
     - STRING
     - Name of the Kubernetes workload
   * - ``results[].kind``
     - STRING
     - Type of Kubernetes resource (Deployment, StatefulSet, etc.)
   * - ``results[].container``
     - STRING
     - Container name within the workload
   * - ``results[].priority``
     - STRING
     - Priority level of the recommendation
   * - ``results[].current_cpu_request``
     - NUMBER
     - Current CPU request in millicores
   * - ``results[].recommended_cpu_request``
     - NUMBER
     - Recommended CPU request in millicores
   * - ``results[].current_cpu_limit``
     - NUMBER
     - Current CPU limit in millicores
   * - ``results[].recommended_cpu_limit``
     - NUMBER
     - Recommended CPU limit in millicores
   * - ``results[].current_memory_request``
     - NUMBER
     - Current memory request in bytes
   * - ``results[].recommended_memory_request``
     - NUMBER
     - Recommended memory request in bytes
   * - ``results[].current_memory_limit``
     - NUMBER
     - Current memory limit in bytes
   * - ``results[].recommended_memory_limit``
     - NUMBER
     - Recommended memory limit in bytes
   * - ``results[].pods_count``
     - INTEGER
     - Number of pods for this workload

**Error Responses**

**401 Unauthorized**

.. code-block:: json

    {
      "error": "Invalid or missing API key"
    }

**400 Bad Request**

.. code-block:: json

    {
      "msg": "Bad query parameters [error details]",
      "error_code": "BAD_PARAMETER"
    }

**500 Internal Server Error**

.. code-block:: json

    {
      "msg": "Failed to query KRR recommendations",
      "error_code": "UNEXPECTED_ERROR"
    }

Reference
======================================
.. robusta-action:: playbooks.robusta_playbooks.krr.krr_scan on_schedule

    You can trigger a KRR scan at any time, by running the following command:

    .. code-block:: bash

        robusta playbooks trigger krr_scan
