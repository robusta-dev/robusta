:hide-toc:

General Settings
================

Connect Robusta to your metrics backend to enable advanced features like alert enrichment with historical data, metric queries, and alert silencing.

.. note::

   Metric provider integration is optional but highly recommended. It enables Robusta to:
   
   • Enrich alerts with relevant metrics and graphs
   • Query historical data for troubleshooting
   • Create and manage alert silences
   • Provide context for AI-powered investigations

Why Configure a Metric Provider?
--------------------------------

When Robusta has access to your metrics:

- **Alert Enrichment** - Automatically attach relevant graphs to alerts
- **Historical Context** - Query past data to understand trends
- **Alert Silencing** - Create and manage silences directly from Robusta
- **AI Insights** - Provide HolmesGPT with metrics for better root cause analysis

Supported Providers
-------------------

.. grid:: 1 1 2 3
    :gutter: 3

    .. grid-item-card:: :octicon:`server;1em;` In-cluster Prometheus
        :class-card: sd-bg-light sd-bg-text-light
        :link: metric-providers-in-cluster
        :link-type: doc

        Standard Prometheus running in your Kubernetes cluster

    .. grid-item-card:: :octicon:`globe;1em;` External Prometheus
        :class-card: sd-bg-light sd-bg-text-light
        :link: metric-providers-external
        :link-type: doc

        Prometheus, Thanos, or Mimir outside your cluster

    .. grid-item-card:: :octicon:`cloud;1em;` Azure Managed
        :class-card: sd-bg-light sd-bg-text-light
        :link: metric-providers-azure
        :link-type: doc

        Azure Monitor managed Prometheus service

    .. grid-item-card:: :octicon:`cloud;1em;` AWS Managed
        :class-card: sd-bg-light sd-bg-text-light
        :link: metric-providers-aws
        :link-type: doc

        Amazon Managed Prometheus (AMP)

    .. grid-item-card:: :octicon:`cloud;1em;` Google Managed
        :class-card: sd-bg-light sd-bg-text-light
        :link: metric-providers-google
        :link-type: doc

        Google Cloud Managed Prometheus

    .. grid-item-card:: :octicon:`database;1em;` Coralogix
        :class-card: sd-bg-light sd-bg-text-light
        :link: metric-providers-coralogix
        :link-type: doc

        Coralogix managed Prometheus

    .. grid-item-card:: :octicon:`database;1em;` VictoriaMetrics
        :class-card: sd-bg-light sd-bg-text-light
        :link: metric-providers-victoria
        :link-type: doc

        VictoriaMetrics time-series database

Common Configuration Options
----------------------------

These settings apply to all metric providers:

Authentication
^^^^^^^^^^^^^^

Add authentication headers as needed:

.. code-block:: yaml

    globalConfig:
        prometheus_auth: "Bearer YOUR_TOKEN"
        alertmanager_auth: "Basic USER:PASS_BASE64"

Multi-tenant Systems
^^^^^^^^^^^^^^^^^^^^

For multi-tenant Prometheus or AlertManager:

.. code-block:: yaml

    globalConfig:
        prometheus_additional_headers:
            X-Scope-OrgID: "your-org-id"
        alertmanager_additional_headers:
            X-Scope-OrgID: "your-org-id"

SSL Configuration
^^^^^^^^^^^^^^^^^

Enable SSL verification:

.. code-block:: yaml

    runner:
        additional_env_vars:
        - name: PROMETHEUS_SSL_ENABLED
          value: "true"
          
        # For custom CA certificates:
        certificate: "BASE64_ENCODED_CA_CERT"

Disable Flags API Check
^^^^^^^^^^^^^^^^^^^^^^^

Robusta uses the Prometheus flags API to verify connectivity. However, some managed services don't implement this API:

- **Azure Managed Prometheus** - Always disable
- **AWS Managed Prometheus** - Always disable
- **Google Managed Prometheus** - Always disable
- **Coralogix** - Always disable
- **Standard Prometheus** - Keep enabled (default)
- **VictoriaMetrics** - Keep enabled (default)

To disable the check:

.. code-block:: yaml

    globalConfig:
        check_prometheus_flags: false

Verification
------------

**Option 1: Robusta UI**
   Open any application in the Robusta UI. If CPU and memory graphs appear, the integration is working.

**Option 2: Test Alert**
   Trigger a demo alert and verify it includes a memory graph:

   .. code-block:: bash

       kubectl apply -f https://raw.githubusercontent.com/robusta-dev/kubernetes-demos/main/oomkill/oomkill_job.yaml

Troubleshooting
---------------

If Robusta can't connect to your metrics provider:

1. Check the logs for connection errors:

   .. code-block:: bash

       kubectl logs -n robusta deployment/robusta-runner

2. Verify the URLs are accessible from within the cluster:

   .. code-block:: bash

       kubectl run test-curl --image=curlimages/curl --rm -it -- \
           curl -v http://prometheus-url:9090/-/healthy

3. Ensure authentication is configured correctly
4. For managed services, verify the ``check_prometheus_flags`` setting

.. tip::

   Having issues? Check our :doc:`troubleshooting guide </help>` or reach out on Slack!