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

.. code-block:: text

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

.. code-block:: bash

    kubectl exec -n <robusta-ns> deploy/robusta-runner -- \
      sh -c 'for host in api.robusta.dev relay.robusta.dev platform.robusta.dev; do
        echo "== $host =="; curl -sS -o /dev/null -w "%{http_code}\n" https://$host/ || true
      done'

A non-zero HTTP code (including ``401``/``404``) confirms TCP + TLS reach the host. Connection timeouts indicate the firewall is still blocking.

Running Robusta in Air-Gapped or Offline Environments
------------------------------------------------------------------------------

Contact support@robusta.dev for self-hosted deployment options that work in fully air-gapped or offline environments (private image registry, on-prem platform, no SaaS dependency).
