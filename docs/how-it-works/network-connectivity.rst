Network Connectivity
=====================

This page documents the network connections made by Robusta and HolmesGPT, the ports and protocols involved, and the firewall or network policy rules you may need when deploying in restricted environments.

For proxy configuration, see :ref:`Deploying Behind Proxies`.

.. _network-overview:

Overview
^^^^^^^^

Robusta's in-cluster agent makes **outbound-only** connections to the Robusta Platform — no inbound access from the internet is required. Within the cluster, Robusta exposes HTTP services that receive webhooks from AlertManager and metrics scrapes from Prometheus.

HolmesGPT runs as a separate deployment and communicates with the Robusta runner over an internal ClusterIP service. HolmesGPT also makes outbound calls to your configured LLM provider and to the Kubernetes API server.

.. _robusta-runner-networking:

Robusta Runner
^^^^^^^^^^^^^^

Inbound (Cluster-Internal)
--------------------------

The runner exposes a single HTTP service inside the cluster:

.. list-table::
   :header-rows: 1
   :widths: 20 15 15 50

   * - Service
     - Port
     - Protocol
     - Purpose
   * - Runner API
     - 80 → 5000
     - HTTP
     - Receives AlertManager webhooks (``/api/alerts``), Kubernetes events from the forwarder (``/api/handle``), manual triggers (``/api/trigger``), and serves a health check (``/healthz``)
   * - Runner Metrics
     - 80 → 5000
     - HTTP
     - Prometheus metrics endpoint (``/metrics``), scraped by ServiceMonitor when enabled

No ``Ingress`` or ``LoadBalancer`` is created by default — the service is ``ClusterIP`` only.

Outbound
--------

.. list-table::
   :header-rows: 1
   :widths: 30 15 55

   * - Destination
     - Port
     - Notes
   * - Kubernetes API server
     - 443
     - Required. Used for reading resources, watching events, and executing playbook actions.
   * - Robusta Platform (SaaS)
     - 443
     - Required when SaaS is enabled. Domains listed below.
   * - Prometheus
     - 9090 (default)
     - Required when Prometheus integration is enabled. In-cluster traffic. Port is configurable.
   * - AlertManager
     - 9093 (default)
     - Optional. Used for alert silencing. In-cluster traffic. Port is configurable.
   * - Grafana
     - 3000 (default)
     - Optional. Used when Grafana enrichments are configured.
   * - Notification sinks (Slack, Teams, PagerDuty, etc.)
     - 443
     - Required for each configured sink. Outbound HTTPS to the sink provider's API.
   * - HolmesGPT service
     - 80 → 5050
     - Required when HolmesGPT is enabled. In-cluster traffic to the ``holmes`` service.
   * - Git repositories
     - 22 / 443
     - Optional. Used when custom playbook repos are configured via SSH or HTTPS.

.. _robusta-saas-domains:

Robusta SaaS Domains
--------------------

If the Robusta SaaS platform is enabled, allow outbound HTTPS (port 443) to:

.. code-block:: text

    api.robusta.dev
    platform.robusta.dev
    relay.robusta.dev
    sp.robusta.dev
    xvyhpoxfmtpuqqeyqkso.supabase.co
    robusta-charts.storage.googleapis.com
    us-central1-docker.pkg.dev

These are also documented in :ref:`Deploying Behind Proxies`.

.. _forwarder-networking:

Forwarder (Kubewatch)
^^^^^^^^^^^^^^^^^^^^^

The forwarder watches Kubernetes events and forwards them to the runner.

.. list-table::
   :header-rows: 1
   :widths: 20 15 15 50

   * - Service
     - Port
     - Protocol
     - Purpose
   * - Forwarder Metrics
     - 80 → 2112
     - HTTP
     - Prometheus metrics endpoint, scraped by ServiceMonitor when enabled

The forwarder makes outbound HTTP calls to the runner service (port 80) and to the Kubernetes API server (port 443).

.. _holmesgpt-networking:

HolmesGPT
^^^^^^^^^^

HolmesGPT runs as a separate ``Deployment`` with its own ``ClusterIP`` service.

Inbound (Cluster-Internal)
--------------------------

.. list-table::
   :header-rows: 1
   :widths: 20 15 15 50

   * - Service
     - Port
     - Protocol
     - Purpose
   * - Holmes API
     - 80 → 5050
     - HTTP
     - Receives investigation requests from the Robusta runner. Endpoints include ``/api/investigate``, ``/api/chat``, ``/api/issue_chat``, and health probes (``/healthz``, ``/readyz``).

Outbound
--------

.. list-table::
   :header-rows: 1
   :widths: 30 15 55

   * - Destination
     - Port
     - Notes
   * - LLM provider API
     - 443
     - Required. Connects to whichever AI provider you configure (OpenAI, Azure OpenAI, AWS Bedrock, GCP Vertex AI, etc.).
   * - Kubernetes API server
     - 443
     - Required. HolmesGPT reads pod logs, events, resource YAML, and other cluster data during investigations.
   * - Prometheus
     - 9090 (default)
     - Required when the ``prometheus/metrics`` toolset is enabled (default). In-cluster traffic.
   * - MCP addon services
     - 8000
     - Optional. In-cluster traffic to MCP sidecar services for AWS, Azure, GCP, GitHub, or MariaDB integrations.

.. _llm-provider-domains:

LLM Provider Domains
---------------------

Allow outbound HTTPS (port 443) to the domain for your chosen provider:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Provider
     - Domain(s)
   * - OpenAI
     - ``api.openai.com``
   * - Azure OpenAI
     - ``<your-resource>.openai.azure.com``
   * - AWS Bedrock
     - ``bedrock-runtime.<region>.amazonaws.com``
   * - GCP Vertex AI
     - ``<region>-aiplatform.googleapis.com``

If you use a custom or self-hosted LLM endpoint, allow access to that endpoint instead.

.. _mcp-addon-networking:

MCP Addon Services (Optional)
------------------------------

When Holmes MCP addons are enabled (e.g., ``mcpAddons.aws.enabled: true``), each addon runs as a separate deployment with a ``ClusterIP`` service on port 8000. Holmes communicates with these addons over in-cluster HTTP.

The addons themselves make outbound calls to cloud provider APIs:

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Addon
     - Outbound Destinations
   * - AWS
     - AWS service endpoints (IAM, CloudWatch, etc.) in your configured region
   * - Azure
     - Azure Resource Manager and related APIs
   * - GCP
     - Google Cloud APIs (``*.googleapis.com``)
   * - GitHub
     - ``api.github.com`` (or your GitHub Enterprise host)
   * - MariaDB
     - Your database host on the configured port (default 3306)

Some MCP addons include optional ``NetworkPolicy`` resources in their Helm templates. These can be enabled per addon (e.g., ``mcpAddons.aws.networkPolicy.enabled: true``) and restrict ingress to only the Holmes pod on port 8000.

.. _network-policies:

Network Policy Guidelines
^^^^^^^^^^^^^^^^^^^^^^^^^^

The Robusta Helm chart does not install ``NetworkPolicy`` resources by default. If your cluster enforces network policies, you will need to create policies that allow the traffic described above.

Below is a summary of the minimum rules needed:

Ingress Rules
-------------

.. list-table::
   :header-rows: 1
   :widths: 25 20 55

   * - Target Pod
     - Allow From
     - Ports
   * - ``robusta-runner``
     - AlertManager pods
     - 5000/TCP
   * - ``robusta-runner``
     - Forwarder (kubewatch) pods
     - 5000/TCP
   * - ``robusta-runner``
     - Prometheus (for scraping ``/metrics``)
     - 5000/TCP
   * - ``holmes``
     - ``robusta-runner`` pods
     - 5050/TCP
   * - ``holmes`` MCP addons
     - ``holmes`` pods
     - 8000/TCP
   * - ``robusta-forwarder``
     - Prometheus (for scraping ``/metrics``)
     - 2112/TCP

Egress Rules
------------

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Source Pod
     - Allow To
   * - ``robusta-runner``
     - Kubernetes API (443), Prometheus (9090), AlertManager (9093), Grafana (3000), Holmes service (80), Robusta SaaS domains (443), configured sinks (443), DNS (53)
   * - ``holmes``
     - Kubernetes API (443), LLM provider (443), Prometheus (9090), MCP addon services (8000), DNS (53)
   * - ``robusta-forwarder``
     - Kubernetes API (443), Runner service (80), DNS (53)
   * - MCP addons
     - Respective cloud provider APIs (443), DNS (53)

.. tip::

   Don't forget to allow DNS (port 53 TCP/UDP) egress in all policies. Kubernetes service discovery and external domain resolution both depend on it.

Example NetworkPolicy
---------------------

The following example allows the Robusta runner to reach Holmes, the Kubernetes API, and external HTTPS endpoints. Adjust selectors and namespaces to match your deployment.

.. code-block:: yaml

    apiVersion: networking.k8s.io/v1
    kind: NetworkPolicy
    metadata:
      name: robusta-runner-egress
      namespace: robusta
    spec:
      podSelector:
        matchLabels:
          app: robusta-runner
      policyTypes:
        - Egress
      egress:
        # DNS
        - ports:
            - port: 53
              protocol: UDP
            - port: 53
              protocol: TCP
        # Kubernetes API server
        - ports:
            - port: 443
              protocol: TCP
        # Holmes service
        - to:
            - podSelector:
                matchLabels:
                  app: holmes
          ports:
            - port: 5050
              protocol: TCP
        # Prometheus (adjust selector to match your Prometheus)
        - ports:
            - port: 9090
              protocol: TCP

.. _air-gapped-environments:

Air-Gapped Environments
^^^^^^^^^^^^^^^^^^^^^^^^

Robusta can run without any internet access if:

- Robusta SaaS is disabled
- No external notification sinks are configured (or sinks point to in-cluster services)
- Container images are available from an internal registry
- HolmesGPT connects to a self-hosted LLM endpoint within the cluster or network

See :ref:`Deploying Behind Proxies` for proxy and air-gapped configuration details.
