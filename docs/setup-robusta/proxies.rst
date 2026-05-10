Deploying Behind Proxies
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If your Kubernetes cluster is behind an HTTP proxy or firewall, follow the instructions below to ensure Robusta and HolmesGPT have the necessary access.

Configuring Proxy Settings
----------------------------------------

Set the ``HTTP_PROXY`` and ``HTTPS_PROXY`` environment variables in your Helm values:

.. code-block:: yaml

    runner:
      additional_env_vars:
        - name: HTTP_PROXY
          value: "http://your-proxy:port"
        - name: HTTPS_PROXY
          value: "http://your-proxy:port"

    holmes:
      additionalEnvVars:
        - name: HTTP_PROXY
          value: "http://your-proxy:port"
        - name: HTTPS_PROXY
          value: "http://your-proxy:port"

To set many variables at once, ``runner.additional_env_froms`` accepts a Kubernetes ``envFrom`` source. See `this GitHub issue <https://github.com/robusta-dev/robusta/pull/450>`_ for details and examples.

.. _firewall-allowlist:

Firewall / DNS Allowlist
----------------------------------------

When deploying Robusta in a tightly restricted environment, the runner needs outbound access to a number of external endpoints. The lists below are organized by feature so you can allow only what you actually use.

A consolidated wildcard list is provided at the bottom for operators who prefer a minimal allowlist.

.. note::
   Traffic is **always initiated outbound from the runner**. No inbound connections to your cluster are required. All endpoints below are reached over HTTPS (TCP/443) unless noted otherwise.

Required: Install & Upgrade Time
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

These endpoints are needed when ``helm install`` / ``helm upgrade`` runs and when the cluster pulls container images. They are not needed at steady-state runtime once images are cached locally.

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Domain
     - Purpose
   * - ``robusta-charts.storage.googleapis.com``
     - Robusta Helm chart repository (``helm repo add robusta ...``)
   * - ``docker.io`` / ``registry-1.docker.io`` / ``auth.docker.io`` / ``production.cloudflare.docker.com``
     - Default registry for ``robustadev/robusta-runner``, ``robustadev/kubewatch``, ``robustadev/grafana-renderer``
   * - ``us-central1-docker.pkg.dev``
     - Registry for HolmesGPT MCP server images and some bundled tooling images
   * - ``quay.io`` (only if you use the bundled ``kube-prometheus-stack`` subchart)
     - Prometheus / Alertmanager / kube-state-metrics images
   * - ``ghcr.io`` (only if you use the bundled ``kube-prometheus-stack`` subchart)
     - Prometheus operator images

If you mirror images to a private registry, override ``image.registry`` (and the per-component ``image:`` fields) in your Helm values and you can drop the public registries from the allowlist.

Required: Robusta SaaS Platform
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Required only if you enable the ``robusta_sink`` (i.e. you are using the Robusta SaaS UI / platform). If you are running Robusta strictly OSS without the platform, none of these are needed.

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Domain
     - Purpose
   * - ``api.robusta.dev``
     - Platform REST API: cluster registration, runner version checks, action relay, telemetry
   * - ``relay.robusta.dev``
     - WebSocket relay (``wss://``) used to deliver platform-initiated actions to the runner. Override with the ``WEBSOCKET_RELAY_ADDRESS`` env var
   * - ``platform.robusta.dev``
     - Robusta UI (links rendered into Slack/Teams/email messages)
   * - ``<your-store-id>.supabase.co``
     - Cluster data store. The exact subdomain is supplied to the runner in your Robusta token (``store_url``). Common default: ``xvyhpoxfmtpuqqeyqkso.supabase.co``
   * - ``sp.robusta.dev``
     - Platform analytics endpoint
   * - ``docs.robusta.dev``
     - Documentation links embedded in some notifications (not strictly required for the runner to function)

Optional: Error Reporting
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Used only when ``runner.sendAdditionalTelemetry`` is enabled or a ``runner.sentry_dsn`` / ``holmes.sentryDSN`` is configured. Default DSNs point to ``ingest.de.sentry.io``.

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Domain
     - Purpose
   * - ``*.ingest.sentry.io`` / ``*.ingest.de.sentry.io``
     - Sentry error reporting. Set ``runner.sentry_dsn: ""`` and ``holmes.sentryDSN: ""`` to disable

Optional: Sink Integrations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Each row applies **only if you enable that specific sink**. Several sinks accept a user-supplied URL (Jira, ServiceNow, Mattermost, RocketChat, Webex, VictorOps, Zulip, generic Webhook, Kafka). For those, allow the host you configured.

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Sink
     - Domains
   * - Slack
     - ``slack.com``, ``hooks.slack.com``, ``files.slack.com``, ``slack-files.com`` (covered by ``*.slack.com`` plus ``slack-files.com``)
   * - Microsoft Teams
     - ``*.webhook.office.com`` (Incoming Webhook), ``*.logic.azure.com`` (Workflows / Power Automate), ``graph.microsoft.com`` (Graph API)
   * - PagerDuty
     - ``events.pagerduty.com``, ``api.pagerduty.com`` (and ``bit.ly`` for shortlinks rendered in messages)
   * - OpsGenie
     - ``api.opsgenie.com`` (or ``api.eu.opsgenie.com`` if you set ``host: eu``)
   * - Jira
     - Your Jira instance (e.g. ``<tenant>.atlassian.net`` or self-hosted hostname)
   * - ServiceNow
     - Your ServiceNow instance (``<instance>.service-now.com``)
   * - Discord
     - ``discord.com`` (webhook URLs are under ``discord.com/api/webhooks/...``)
   * - Telegram
     - ``api.telegram.org`` (override with ``TELEGRAM_BASE_URL`` if using a self-hosted Bot API)
   * - Datadog
     - ``api.datadoghq.com`` or your regional endpoint (``api.datadoghq.eu``, ``api.us3.datadoghq.com``, ``api.us5.datadoghq.com``, ``api.ap1.datadoghq.com``)
   * - Pushover
     - ``api.pushover.net``
   * - Incident.io
     - ``api.incident.io``
   * - Webex
     - ``webexapis.com`` (or your Webex webhook host)
   * - Mattermost
     - Your Mattermost server hostname
   * - RocketChat
     - Your RocketChat server hostname
   * - VictorOps / Splunk OnCall
     - ``alert.victorops.com`` (or your configured webhook host)
   * - Zulip
     - Your Zulip server hostname
   * - Yandex Messenger
     - ``botapi.messenger.yandex.net`` (override with ``YM_API_BASE_URL``)
   * - Generic Webhook
     - Your configured destination URL
   * - Kafka
     - Your Kafka broker host(s) (TCP/9092 or your configured port; not HTTPS)
   * - Robusta sink
     - See "Robusta SaaS Platform" above

Optional: HolmesGPT (AI Investigations)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

HolmesGPT runs as an in-cluster service (the ``holmes`` Deployment), so the runner reaches it on a cluster-internal address (``http://holmes:<port>``) — no external allowlist needed for the runner-to-Holmes traffic itself.

Holmes itself, however, calls out to whatever LLM provider you configure. Allow only the provider(s) you actually use:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Provider
     - Domains
   * - OpenAI
     - ``api.openai.com``
   * - Anthropic
     - ``api.anthropic.com``
   * - Azure OpenAI
     - ``<your-resource>.openai.azure.com``, ``login.microsoftonline.com``
   * - AWS Bedrock
     - ``bedrock-runtime.<region>.amazonaws.com``, ``sts.amazonaws.com``
   * - Google Vertex AI / Gemini
     - ``*.googleapis.com`` (specifically ``aiplatform.googleapis.com`` and/or ``generativelanguage.googleapis.com``), ``oauth2.googleapis.com``
   * - Robusta-hosted AI
     - ``api.robusta.dev`` (already listed above)

Optional: Cloud / Observability Auth
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Only required if you connect the runner to one of these managed observability backends:

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Domain
     - Purpose
   * - ``login.microsoftonline.com``
     - Azure AD OAuth token endpoint (Azure Managed Prometheus, Azure OpenAI)
   * - ``prometheus.monitor.azure.com``
     - Azure Managed Prometheus query endpoint
   * - ``169.254.169.254`` (link-local, not DNS)
     - Cloud instance metadata service (Azure / AWS / GCP managed identity). This is in-VPC, not internet, but some egress policies still block it

Wildcard Allowlist (Compact Form)
----------------------------------------

If you can't enumerate every host above, the following wildcard set covers the typical Robusta + HolmesGPT deployment with the Robusta SaaS UI plus the most common sinks. Trim to fit your enabled features.

.. code-block:: text

    # Robusta SaaS platform (required if robusta_sink enabled)
    *.robusta.dev
    *.supabase.co

    # Install / upgrade
    robusta-charts.storage.googleapis.com
    *.docker.io
    us-central1-docker.pkg.dev
    quay.io
    ghcr.io

    # Error reporting (optional)
    *.sentry.io

    # Sinks (only those you enable)
    *.slack.com
    slack-files.com
    *.office.com
    *.logic.azure.com
    *.pagerduty.com
    *.opsgenie.com
    *.atlassian.net
    *.service-now.com
    *.datadoghq.com
    *.datadoghq.eu
    discord.com
    api.telegram.org
    api.pushover.net
    api.incident.io
    webexapis.com

    # HolmesGPT LLM providers (only those you use)
    api.openai.com
    api.anthropic.com
    *.openai.azure.com
    login.microsoftonline.com
    *.amazonaws.com
    *.googleapis.com

Verifying the Allowlist
----------------------------------------

After applying firewall rules, you can sanity-check connectivity from inside the runner pod:

.. code-block:: bash

    kubectl exec -n <robusta-ns> deploy/robusta-runner -- \
      sh -c 'for host in api.robusta.dev relay.robusta.dev platform.robusta.dev; do
        echo "== $host =="; curl -sS -o /dev/null -w "%{http_code}\n" https://$host/ || true
      done'

A non-zero HTTP code (including ``401``/``404``) confirms TCP + TLS reach the host. Connection timeouts indicate the firewall is still blocking.

Running Robusta in Air-Gapped or Offline Environments
------------------------------------------------------------------------------

Contact support@robusta.dev for self-hosted deployment options that work in fully air-gapped or offline environments (private image registry, on-prem platform, no SaaS dependency).
