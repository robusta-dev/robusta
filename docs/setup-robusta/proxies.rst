Deploying Behind Proxies
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If your Kubernetes cluster is behind an HTTP proxy or firewall, follow the instructions below to ensure Robusta has the necessary access.

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

To set many variables at once, ``runner.additional_env_froms`` accepts a Kubernetes ``envFrom`` source. See `this GitHub issue <https://github.com/robusta-dev/robusta/pull/450>`_ for details and examples.

.. _firewall-allowlist:

Firewall / DNS Allowlist
----------------------------------------

When deploying Robusta in a tightly restricted environment, the runner needs outbound access to a number of external endpoints. The lists below are split by when the access is needed — at runtime, during installation, or only for optional add-ons — so you can allow only what you actually use. Under each wildcard, the specific hosts it expands to are listed indented so you can pick exact hostnames instead of a wildcard if your firewall requires it.

.. note::
   Traffic is **always initiated outbound from the runner**. No inbound connections to your cluster are required. All endpoints are reached over HTTPS (TCP/443) unless noted otherwise.

Runtime
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Reached whenever the runner is running:

.. code-block:: text

    api.robusta.dev          # telemetry, identified by SHA-256 hashes of the account ID and cluster name; set ENABLE_TELEMETRY=false in runner.additional_env_vars to turn it off
    docs.robusta.dev         # doc links embedded in notifications (not strictly required)

Installation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

    # Install / upgrade (only needed during helm install/upgrade and image pulls)
    robusta-charts.storage.googleapis.com   # Robusta Helm chart repository
    *.docker.io                             # default registry for robustadev/* images
        registry-1.docker.io
        auth.docker.io
        production.cloudflare.docker.com
    quay.io                                 # only with bundled kube-prometheus-stack subchart
    ghcr.io                                 # only with bundled kube-prometheus-stack subchart

Add-ons
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Only needed for the integrations and features you actually enable.

.. code-block:: text

    # Error reporting (only if runner.sentry_dsn is set; default points to .de.sentry.io)
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

    # Azure AD OAuth (only with Azure Managed Prometheus)
    login.microsoftonline.com

    # Cloud / observability auth (only if you use these managed backends)
    prometheus.monitor.azure.com            # Azure Managed Prometheus query endpoint
    169.254.169.254                         # cloud instance metadata (Azure/AWS/GCP managed identity)

If you mirror images to a private registry, override ``image.registry`` (and the per-component ``image:`` fields) in your Helm values and you can drop the public registries from the allowlist.

If your private registry requires authentication, set ``global.imagePullSecrets``. This applies the
pull secret to the runner, kubewatch, and the pods the runner launches at runtime (e.g. KRR, Popeye,
via the runner ServiceAccount):

.. code-block:: yaml

    global:
      imagePullSecrets:
        - name: my-registry-secret

A per-component value (e.g. ``runner.imagePullSecrets``, ``kubewatch.imagePullSecrets``)
overrides the global one for that component. Leaving
``global.imagePullSecrets`` empty keeps the previous behavior.

Verifying the Allowlist
----------------------------------------

After applying firewall rules, you can sanity-check connectivity from inside the runner pod:

.. code-block:: bash

    kubectl exec -n <robusta-ns> deploy/robusta-runner -- \
      sh -c 'for host in api.robusta.dev docs.robusta.dev; do
        echo "== $host =="; curl -sS -o /dev/null -w "%{http_code}\n" https://$host/ || true
      done'

A non-zero HTTP code (including ``401``/``404``) confirms TCP + TLS reach the host. Connection timeouts indicate the firewall is still blocking.


Running Robusta in Air-Gapped or Offline Environments
------------------------------------------------------------------------------

Contact support@robusta.dev for self-hosted deployment options that work in fully air-gapped or offline environments (private image registry, on-prem platform, no SaaS dependency).
