Cost Savings (KRR)
************************************************************

`KRR <https://github.com/robusta-dev/krr>`_ is a CLI tool that optimizes resource allocation in Kubernetes clusters.
It gathers pod usage data from Prometheus and recommends requests and limits for CPU and memory, reducing costs and improving performance.

Robusta runs a weekly KRR scan. You can view the scans from all your clusters in the Robusta UI.


.. _krr-cronjob:

Weekly KRR Scan CronJob
===========================================

The Helm chart creates a ``CronJob`` named ``<release>-krr`` that runs the weekly KRR scan and sends the result
to the Robusta UI. It runs with the runner service account, unless ``serviceAccountName`` is set.

The CronJob uses the settings under ``runner.krrCronJob`` and the Prometheus address in ``globalConfig.prometheus_url``.
It uses no other ``globalConfig`` setting, and no runner environment variable:

.. code-block:: yaml

    runner:
      krrCronJob:
        enabled: ~               # empty: on with enablePlatformPlaybooks, unless rbac.disableCreateFromServiceAccount is true
        schedule: "0 12 * * 1"   # every Monday at 12:00
        timeout: 3600            # seconds
        image: ~                 # defaults to image.registry/krr
        strategy: simple
        krrArgs: ""              # extra KRR arguments
        memoryRequest: 2Gi
        memoryLimit: 2Gi
        jobSpec: {}              # tolerations, nodeSelector, affinity...
        annotations: {}          # added to the KRR Job and pod
        serviceAccountName: ~    # an existing service account. Defaults to the runner's
        additional_env_vars: []  # env vars of the KRR pod
        additional_env_froms: [] # env sources of the KRR pod

By default, the CronJob is created only when ``enablePlatformPlaybooks`` is ``true``. Set ``runner.krrCronJob.enabled: true`` to create it
without platform playbooks. The CronJob is not created without a Robusta UI sink, or when ``WeeklyKRRScan`` is listed in ``disabledPlaybooks``.

Without ``globalConfig.prometheus_url``, KRR finds Prometheus in the cluster by itself. To use another address for KRR, add ``-p <url>`` to ``krrArgs``.

Credentials for the KRR CronJob
------------------------------------------------------------

If your Prometheus needs credentials, set them for KRR under ``runner.krrCronJob``, or the weekly scan fails. The
Prometheus credentials, headers and labels under ``globalConfig`` and the runner's ``additional_env_vars`` are not passed to KRR.

``krrArgs`` runs in a shell, so ``"$NAME"`` reads an environment variable of the KRR pod.

.. warning::

    Never write a credential itself into ``krrArgs``. The CronJob object is readable in the cluster, so anyone who can view it would see the value. Always reference an environment variable that comes from a Secret, as the examples below do.

**Prometheus with a token:**

.. code-block:: yaml

    runner:
      krrCronJob:
        krrArgs: '--prometheus-auth-header "Bearer $PROMETHEUS_TOKEN"'
        additional_env_vars:
        - name: PROMETHEUS_TOKEN
          valueFrom:
            secretKeyRef:
              name: prometheus-credentials
              key: token


**AWS Managed Prometheus:**

.. code-block:: yaml

    globalConfig:
      prometheus_url: https://aps-workspaces.us-east-1.amazonaws.com/workspaces/ws-12345678

    runner:
      krrCronJob:
        krrArgs: '--eks-managed-prom --eks-managed-prom-region us-east-1 --eks-access-key "$AWS_ACCESS_KEY" --eks-secret-key "$AWS_SECRET_ACCESS_KEY"'
        additional_env_vars:
        - name: AWS_ACCESS_KEY
          valueFrom:
            secretKeyRef:
              name: aws-credentials
              key: access-key
        - name: AWS_SECRET_ACCESS_KEY
          valueFrom:
            secretKeyRef:
              name: aws-credentials
              key: secret-key

Moving Existing KRR Settings
------------------------------------------------------------

Settings that the weekly scan used before, and where to set them for the CronJob. The right column is under ``runner.krrCronJob`` unless it says otherwise:

.. list-table::
   :widths: 40 60
   :header-rows: 1

   * - Previous setting
     - CronJob setting
   * - ``globalConfig.krr_args``
     - ``krrArgs``
   * - ``globalConfig.strategy``, ``KRR_STRATEGY``
     - ``strategy``
   * - ``globalConfig.timeout``
     - ``timeout``
   * - ``globalConfig.max_workers``
     - ``krrArgs: "--max-workers 2"``
   * - ``globalConfig.krr_verbose``
     - ``krrArgs: "-v"``
   * - ``globalConfig.krr_job_spec``
     - ``jobSpec``
   * - ``globalConfig.prometheus_url``
     - Still used. To use another address for KRR: ``krrArgs: "-p <url>"``
   * - ``globalConfig.prometheus_auth``
     - ``krrArgs: '--prometheus-auth-header "$PROMETHEUS_AUTH"'``, with the value in ``additional_env_vars``
   * - ``globalConfig.prometheus_additional_headers``
     - ``krrArgs: '--prometheus-headers "X-Scope-OrgID:$ORG_ID"'``, once for each header
   * - ``globalConfig.prometheus_additional_labels``
     - ``krrArgs: "--prometheus-label cluster -l my-cluster"``
   * - ``AWS_REGION``, ``AWS_SERVICE_NAME``, ``AWS_ASSUME_ROLE``
     - ``krrArgs: "--eks-managed-prom --eks-managed-prom-region <region> --eks-service-name <name> --eks-assume-role <arn>"``
   * - ``AWS_ACCESS_KEY``, ``AWS_SECRET_ACCESS_KEY``
     - ``krrArgs: '--eks-access-key "$AWS_ACCESS_KEY" --eks-secret-key "$AWS_SECRET_ACCESS_KEY"'``, with the values in ``additional_env_vars``
   * - ``CORALOGIX_PROMETHEUS_TOKEN``
     - ``krrArgs: '--coralogix-token "$CORALOGIX_PROMETHEUS_TOKEN"'``, with the value in ``additional_env_vars``
   * - OpenShift, ``PROMETHEUS_CLUSTER_TOKEN_AUTH``
     - ``krrArgs: "--openshift"``
   * - ``KRR_IMAGE_OVERRIDE``
     - ``image``
   * - ``KRR_MEMORY_REQUEST``, ``KRR_MEMORY_LIMIT``
     - ``memoryRequest``, ``memoryLimit``
   * - ``SET_KRR_SECURITY_CONTEXT``
     - ``runner.setKRRSecurityContext``
   * - ``globalConfig.serviceAccountName``
     - ``serviceAccountName``
   * - ``globalConfig.custom_annotations``
     - ``annotations``
   * - ``KRR_PUBLISH_URL``, ``KRR_PUSH_SCAN``
     - No setting

To run a scan now, and to check previous runs (replace ``robusta`` with your release name and namespace):

.. code-block:: bash

    kubectl create job --from=cronjob/robusta-krr krr-manual -n robusta
    kubectl get jobs -l app=krr.robusta.dev -n robusta

Limitations of the CronJob:

- **Azure Managed Prometheus**: authentication with ``AZURE_CLIENT_ID``/``AZURE_TENANT_ID`` and ``AZURE_CLIENT_SECRET`` or ``AZURE_USE_MANAGED_ID`` is not supported. Provide a token as shown above
- **Log mode**: ``KRR_PUSH_SCAN=false`` is not supported
- **Failed runs**: a run that is killed (out of memory, timeout) is not reported to the Robusta UI. KRR still reports its own input and Prometheus errors. Check the Jobs with the command above

Taints, Tolerations and NodeSelectors
============================================

To run KRR on an ARM cluster or on specific nodes you can set custom tolerations or a nodeSelector in your ``generated_values.yaml`` file as follows:

.. code-block:: yaml
    :name: cb-krr-set-custom-taints

    runner:
      krrCronJob:
        jobSpec:
          tolerations:
          - key: "key1"
            operator: "Exists"
            effect: "NoSchedule"
          nodeSelector:
            nodeName: "your-selector"

Customizing Efficiency Recommendations in the Robusta UI
====================================================================================
You can tweak KRR's recommendation algorithm to suit your environment using the ``runner.krrCronJob.krrArgs`` setting in Robusta's Helm chart.

Add the following config to the top of your ``generated_values.yaml`` with your custom values. KRR will use these values every time it sends data to the Robusta UI.

If you are having performance issues, specifically with Prometheus using a lot of memory, reduce ``--max-workers`` to reduce memory usage. KRR uses 3 workers by default.

.. code-block:: yaml

    runner:
      krrCronJob:
        krrArgs: "--cpu-min 15 --mem-min 200 --cpu_percentile 90 --memory_buffer_percentage 25 --max-workers 2"

Enabling HPA Recommendations in the Robusta UI
------------------------------------------------------------
To enable Horizontal Pod Autoscaler (HPA) recommendations in the Robusta UI, add the following to your ``generated_values.yaml`` file:

.. code-block:: yaml

    runner:
      krrCronJob:
        krrArgs: "--allow-hpa"

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

To prevent the KRR job from OOMKill (Out of Memory), you can configure the memory requests and limits by adding the following to your ``generated_values.yaml`` file:

.. code-block:: yaml

    runner:
      krrCronJob:
        memoryRequest: "3Gi"
        memoryLimit: "3Gi"

By default, the memory request and limit are set to ``2Gi``. Modify these values according to your requirements.

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
