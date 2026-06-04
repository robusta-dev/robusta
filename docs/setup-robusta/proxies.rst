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

When deploying Robusta in a tightly restricted environment, the runner needs outbound access to a number of external endpoints. The list below is organized by feature so you can allow only what you actually use. Under each wildcard, the specific hosts it expands to are listed indented so you can pick exact hostnames instead of a wildcard if your firewall requires it.

.. note::
   Traffic is **always initiated outbound from the runner**. No inbound connections to your cluster are required. All endpoints are reached over HTTPS (TCP/443) unless noted otherwise.

.. robusta-code:: text

    # Robusta SaaS platform (required if robusta_sink enabled)
    *.robusta.dev
        api.robusta.dev          # platform REST API: cluster registration, action relay, telemetry
        relay.robusta.dev        # WebSocket relay (wss://); override with WEBSOCKET_RELAY_ADDRESS
        platform.robusta.dev     # Robusta UI (links rendered into Slack/Teams/email)
        sp.robusta.dev           # platform analytics
        docs.robusta.dev         # doc links embedded in notifications (not strictly required)
    *.supabase.co                # cluster data store; exact subdomain comes from your token's store_url

    # Install / upgrade (only needed during helm install/upgrade and image pulls)
    robusta-charts.storage.googleapis.com   # Robusta Helm chart repository
    *.docker.io                             # default registry for robustadev/* images
        registry-1.docker.io
        auth.docker.io
        production.cloudflare.docker.com
    us-central1-docker.pkg.dev              # HolmesGPT MCP server images and bundled tooling
    quay.io                                 # only with bundled kube-prometheus-stack subchart
    ghcr.io                                 # only with bundled kube-prometheus-stack subchart

    # Error reporting (only if runner.sentry_dsn / holmes.sentryDSN is set; default points to .de.sentry.io)
    *.sentry.io
        *.ingest.sentry.io
        *.ingest.de.sentry.io

    # Sinks (only those you enable)
    *.slack.com
        slack.com
        hooks.slack.com
        files.slack.com
    slack-files.com                         # Slack file uploads
    *.office.com                            # Microsoft Teams Incoming Webhook
    *.logic.azure.com                       # Microsoft Teams Workflows / Power Automate
    graph.microsoft.com                     # Microsoft Teams Graph API
    *.pagerduty.com
        events.pagerduty.com
        api.pagerduty.com
    *.opsgenie.com
        api.opsgenie.com
        api.eu.opsgenie.com                 # if host: eu
    *.atlassian.net                         # Jira (your tenant subdomain)
    *.service-now.com                       # ServiceNow (your instance subdomain)
    *.datadoghq.com
        api.datadoghq.com
        api.us3.datadoghq.com
        api.us5.datadoghq.com
        api.ap1.datadoghq.com
    *.datadoghq.eu                          # Datadog EU region
    discord.com                             # webhooks under discord.com/api/webhooks/...
    api.telegram.org                        # override with TELEGRAM_BASE_URL for self-hosted Bot API
    api.pushover.net
    api.incident.io
    webexapis.com
    alert.victorops.com                     # VictorOps / Splunk OnCall
    botapi.messenger.yandex.net             # Yandex (override with YM_API_BASE_URL)
    # Mattermost, RocketChat, Zulip, generic Webhook, Kafka: allow the host you configured

    # HolmesGPT LLM providers (only those you use)
    api.openai.com                          # OpenAI
    api.anthropic.com                       # Anthropic
    *.openai.azure.com                      # Azure OpenAI (your resource subdomain)
    login.microsoftonline.com               # Azure AD OAuth (Azure OpenAI / Azure Managed Prometheus)
    *.amazonaws.com                         # AWS Bedrock
        bedrock-runtime.<region>.amazonaws.com
        sts.amazonaws.com
    *.googleapis.com                        # Google Vertex AI / Gemini
        aiplatform.googleapis.com
        generativelanguage.googleapis.com
        oauth2.googleapis.com

    # Cloud / observability auth (only if you use these managed backends)
    prometheus.monitor.azure.com            # Azure Managed Prometheus query endpoint
    169.254.169.254                         # cloud instance metadata (Azure/AWS/GCP managed identity)

If you mirror images to a private registry, override ``image.registry`` (and the per-component ``image:`` fields) in your Helm values and you can drop the public registries from the allowlist.

Verifying the Allowlist
----------------------------------------

After applying firewall rules, you can sanity-check connectivity from inside the runner pod:

.. robusta-code:: bash

    kubectl exec -n <robusta-ns> deploy/robusta-runner -- \
      sh -c 'for host in api.robusta.dev relay.robusta.dev platform.robusta.dev; do
        echo "== $host =="; curl -sS -o /dev/null -w "%{http_code}\n" https://$host/ || true
      done'

A non-zero HTTP code (including ``401``/``404``) confirms TCP + TLS reach the host. Connection timeouts indicate the firewall is still blocking.

Copying Images to a Private Image Registry
------------------------------------------

If you are running the Robusta **self-hosted platform** (the ``robusta-platform`` Helm chart) in an environment that cannot pull from public registries (Docker Hub, ``us-central1-docker.pkg.dev``, ``quay.io``), mirror the images below to your internal registry and override the registry fields in your Helm values.

The list reflects the images pulled by the chart at the versions shipped in the current release. Image tags change between chart versions — re-check ``values.yaml`` of the chart version you are installing.

**Images from the Robusta registry** (default: ``us-central1-docker.pkg.dev/genuine-flight-317411/devel``)

.. robusta-code:: text

    robusta-db:14.1.1            # Supabase Postgres 14 (default DB image)
    robusta-db:15.0.0            # Supabase Postgres 15 (only if usePostgres15=true)
    db-migration:0.0.66          # DB migration init Job
    realtime:v2.96.0             # Robusta fork of supabase/realtime (JWT_REQUIRE_EXP)
    platform-relay:0.22.0        # Relay (WebSocket + API)  — only if enableRelay=true
    robusta-ui:0.2.87            # Platform UI              — only if enableRobustaUI=true
    rbac-import:0.3.0            # Optional RBAC import CronJob (rbacImport.enabled)

**Images from Docker Hub** (controlled by ``dockerRegistry``)

.. robusta-code:: text

    supabase/gotrue:v2.189.0
    supabase/postgres-meta:v0.96.5
    supabase/studio:2026.05.11-sha-5a5099a
    postgrest/postgrest:v14.6
    kong:3.9.1
    postgres:15-alpine                  # realtime schema-init container
    busybox:1.37                        # init containers for rest/meta/migration

**Optional images** (only if the corresponding feature is enabled)

.. robusta-code:: text

    quay.io/prometheuscommunity/postgres-exporter:v0.15.0   # monitoring.postgresExporter.enabled

After mirroring, point the chart at your registry by overriding the following values:

.. code-block:: yaml

    # Robusta-built images
    robustaRegistry: my-registry.example.com/robusta

    # Public images — value is used as a prefix, so include the trailing slash
    dockerRegistry: my-registry.example.com/

    # Subchart registries (robusta-ui and robusta-relay are dependencies)
    robusta-ui:
      registry: my-registry.example.com/robusta
    robusta-relay:
      registry: my-registry.example.com/robusta

    # Monitoring image is a full path — override directly if enabled
    monitoring:
      postgresExporter:
        image: my-registry.example.com/prometheuscommunity/postgres-exporter:v0.15.0

    # If your registry requires auth
    imagePullSecrets:
      - name: my-registry-secret

.. tip::

    **Override the registry, not the tags.** The chart exposes per-image fields
    (``dbImage``, ``authImage``, ``realtimeImage``, ``migrationImage``, etc.) but
    these are intended for internal use — they pin the exact tags that have been
    tested with the current chart version. If you pin them yourself, every chart
    upgrade will silently roll your images back to the tags you hard-coded, and
    you will need to bump each one by hand on every release.

    For mirrored-registry setups, override only ``robustaRegistry`` /
    ``dockerRegistry`` (and the matching subchart ``registry`` fields). The chart
    will continue to use the image tags shipped with each version, just pulled
    from your private registry — so ``helm upgrade`` keeps working seamlessly.
    Your mirroring workflow only needs to re-pull the new tags from
    ``values.yaml`` before each upgrade.

Running Robusta in Air-Gapped or Offline Environments
------------------------------------------------------------------------------

Contact support@robusta.dev for self-hosted deployment options that work in fully air-gapped or offline environments (private image registry, on-prem platform, no SaaS dependency).
