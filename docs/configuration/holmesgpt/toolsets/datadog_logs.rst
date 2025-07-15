.. _toolset_datadog_logs:

Datadog logs
============

By enabling this toolset, HolmesGPT will fetch pod logs from `Datadog <https://www.datadoghq.com/>`_.

You **should** enable this toolset to replace the default :ref:`kubernetes/logs <toolset_kubernetes_logs>`
toolset if all your kubernetes pod logs are consolidated inside Datadog. It will make it easier for HolmesGPT
to fetch incident logs, including the ability to precisely consult past logs.


.. include:: ./_toolsets_that_provide_logging.inc.rst

Configuration
^^^^^^^^^^^^^

.. md-tab-set::

  .. md-tab-item:: Robusta Helm Chart

    .. code-block:: yaml

      holmes:
        toolsets:
          datadog/logs:
            enabled: true
            config:
              dd_api_key: <your-datadog-api-key> # Required. Your Datadog API key
              dd_app_key: <your-datadog-app-key> # Required. Your Datadog Application key
              site_api_url: https://api.datadoghq.com # Required. Your Datadog site URL (e.g. https://api.us3.datadoghq.com for US3)
              indexes: ["*"] # Optional. List of Datadog indexes to search. Default: ["*"]
              storage_tiers: ["indexes"] # Optional. Ordered list of storage tiers to query (fallback mechanism). Options: "indexes", "online-archives", "flex". Default: ["indexes"]
              labels: # Optional. Map Datadog labels to Kubernetes resources
                pod: "pod_name"
                namespace: "kube_namespace"
              page_size: 300 # Optional. Number of logs per API page. Default: 300
              default_limit: 1000 # Optional. Default maximum logs to fetch when limit not specified by the LLM. Default: 1000
              request_timeout: 60 # Optional. API request timeout in seconds. Default: 60

          kubernetes/logs:
            enabled: false # HolmesGPT's default logging mechanism MUST be disabled


    .. include:: ./_toolset_configuration.inc.rst

  .. md-tab-item:: Holmes CLI

    Add the following to **~/.holmes/config.yaml**, creating the file if it doesn't exist:

    .. code-block:: yaml

      toolsets:
        datadog/logs:
          enabled: true
          config:
            dd_api_key: <your-datadog-api-key> # Required. Your Datadog API key
            dd_app_key: <your-datadog-app-key> # Required. Your Datadog Application key
            site_api_url: https://api.datadoghq.com # Required. Your Datadog site URL (e.g. https://api.us3.datadoghq.com for US3)
            indexes: ["*"] # Optional. List of Datadog indexes to search. Default: ["*"]
              storage_tiers: ["indexes"] # Optional. Ordered list of storage tiers to query (fallback mechanism). Options: "indexes", "online-archives", "flex". Default: ["indexes"]
            labels: # Optional. Map Datadog labels to Kubernetes resources
              pod: "pod_name"
              namespace: "kube_namespace"
            page_size: 300 # Optional. Number of logs per API page. Default: 300
            default_limit: 1000 # Optional. Default maximum logs to fetch when limit not specified by the LLM. Default: 1000
            request_timeout: 60 # Optional. API request timeout in seconds. Default: 60

        kubernetes/logs:
          enabled: false # HolmesGPT's default logging mechanism MUST be disabled

Getting API and Application Keys
********************************

To use this toolset, you need both a Datadog API key and Application key:

1. **API Key**: Go to Organization Settings > API Keys in your Datadog console
   
   * The API key must have the ``logs_read_data`` permission scope
   * When creating a new key, ensure this permission is enabled

2. **Application Key**: Go to Organization Settings > Application Keys in your Datadog console

For more information, see the `Datadog API documentation <https://docs.datadoghq.com/api/latest/authentication/>`_.

Configuring Site URL
********************

The ``site_api_url`` must match your Datadog site. Common values include:

* ``https://api.datadoghq.com`` - US1
* ``https://api.us3.datadoghq.com`` - US3
* ``https://api.us5.datadoghq.com`` - US5
* ``https://api.datadoghq.eu`` - EU
* ``https://api.ap1.datadoghq.com`` - AP1

For a complete list of site URLs, see the `Datadog site documentation <https://docs.datadoghq.com/getting_started/site/>`_.

Configuring Storage Tiers
*************************

Datadog offers different storage tiers for logs with varying retention and costs:

.. list-table::
   :header-rows: 1
   :widths: 20 40 40

   * - Storage Tier
     - Description
     - Use Case
   * - indexes
     - Hot storage for recent logs (default)
     - Real-time analysis and alerting
   * - online-archives
     - Warm storage for older logs
     - Historical log analysis
   * - flex
     - Cost-effective storage
     - Long-term retention

The toolset uses storage tiers as a fallback mechanism. Subsequent tiers are queried only if the previous tier yielded no result.
For example if the toolset is configured with storage_tiers ``["indexes", "online-archives"]``, then:

* Holmes first runs a query using storage_tier ``indexes``
* If there are no results at all, Holmes will then query ``online-archives``

Handling Rate Limits
********************

If you encounter rate limiting issues with Datadog (visible as warning messages in Holmes logs), you can adjust the following parameters:

* **page_size**: Reduce this value to fetch fewer logs per API request. This helps avoid hitting rate limits on individual requests.
* **default_limit**: Lower this value to reduce the total number of logs fetched when no explicit limit is specified.

Example configuration for rate-limited environments:

.. code-block:: yaml

  toolsets:
    datadog/logs:
      enabled: true
      config:
        page_size: 100        # Reduced from default 300
        default_limit: 500    # Reduced from default 1000

When rate limiting occurs, Holmes will automatically retry with exponential backoff. You'll see warnings like:
``DataDog logs toolset is rate limited/throttled. Waiting X.Xs until reset time``

Configuring Labels
******************

You can customize the labels used by the toolset to identify Kubernetes resources. This is **optional** and only needed if your
Datadog logs use different field names than the defaults.

.. code-block:: yaml

  toolsets:
    datadog/logs:
      enabled: true
      config:
        labels:
          pod: "pod_name"        # The field name for Kubernetes pod name in your Datadog logs
          namespace: "kube_namespace"  # The field name for Kubernetes namespace in your Datadog logs

To find the correct field names in your Datadog logs:

1. Go to Logs > Search in your Datadog console
2. View a sample log entry
3. Identify the field names used for pod name and namespace
4. Update the labels configuration accordingly

.. include:: ./_disable_default_logging_toolset.inc.rst


Capabilities
^^^^^^^^^^^^

.. include:: ./_toolset_capabilities.inc.rst

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Tool Name
     - Description
   * - fetch_pod_logs
     - Retrieve logs from Datadog with support for filtering, time ranges, and multiple storage tiers