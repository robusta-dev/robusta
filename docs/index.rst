:hide-toc:

.. toctree::
   :maxdepth: 1
   :caption: 📖 Overview
   :hidden:

   self
   how-it-works/architecture
   how-it-works/oss-vs-saas
   how-it-works/usage-faq
   how-it-works/alert-builtin-enrichment

.. toctree::
   :maxdepth: 4
   :caption: 🚀 Installation
   :hidden:

   setup-robusta/index

.. toctree::
   :maxdepth: 4
   :caption: 🚨 Alert Sources
   :hidden:

   Overview <configuration/index>
   Prometheus & AlertManager <configuration/alertmanager-integration/index>
   New Relic <configuration/alertmanager-integration/newrelic>
   SolarWinds <configuration/alertmanager-integration/solarwinds>
   PagerDuty <configuration/alertmanager-integration/pagerduty-alerting>
   Dynatrace <configuration/alertmanager-integration/dynatrace>
   LaunchDarkly <configuration/alertmanager-integration/launchdarkly>
   Nagios <configuration/alertmanager-integration/nagios>
   Custom Webhooks <configuration/exporting/custom-webhooks>

.. toctree::
   :maxdepth: 4
   :caption: 📊 Metric Providers
   :hidden:

   General Settings <configuration/metric-providers>
   In-cluster Prometheus <configuration/metric-providers-in-cluster>
   External Prometheus <configuration/metric-providers-external>
   Azure Managed <configuration/metric-providers-azure>
   AWS Managed <configuration/metric-providers-aws>
   Google Managed <configuration/metric-providers-google>
   Coralogix <configuration/metric-providers-coralogix>
   VictoriaMetrics <configuration/metric-providers-victoria>

.. toctree::
   :maxdepth: 4
   :caption: 🔔 Notification Sinks
   :hidden:

   Overview <notification-routing/configuring-sinks>
   All Sinks <configuration/sinks/index>
   configuration/sinks/slack
   configuration/sinks/ms-teams
   configuration/sinks/RobustaUI
   configuration/sinks/mail
   configuration/sinks/telegram
   configuration/sinks/discord
   configuration/sinks/DataDog
   configuration/sinks/mattermost
   configuration/sinks/Opsgenie
   configuration/sinks/PagerDuty
   configuration/sinks/VictorOps
   configuration/sinks/YandexMessenger
   configuration/sinks/jira
   configuration/sinks/webhook
   configuration/sinks/file
   configuration/sinks/webex
   configuration/sinks/kafka
   configuration/sinks/rocketchat
   configuration/sinks/google_chat
   configuration/sinks/pushover
   configuration/sinks/ServiceNow
   configuration/sinks/zulip
   configuration/sinks/sinks-development

.. toctree::
   :maxdepth: 4
   :caption: 🔀 Alert Routing
   :hidden:

   Overview <notification-routing/index>
   Routing (Scopes) <notification-routing/routing-with-scopes>
   Grouping (Slack Threads) <notification-routing/notification-grouping>
   notification-routing/routing-by-time
   notification-routing/routing-by-namespace
   notification-routing/routing-by-type
   notification-routing/implementing-monitoring-shifts
   notification-routing/routing-to-multiple-slack-channels
   notification-routing/routing-exclusion
   notification-routing/routing-by-severity
   notification-routing/excluding-resolved
   notification-routing/disable-oomkill-notifications
   notification-routing/routing-silencing

.. toctree::
   :maxdepth: 4
   :caption: ⚙️ Automation
   :hidden:

   playbook-reference/index
   configuration/alertmanager-integration/alert-custom-prometheus
   Cost Savings - KRR <configuration/resource-recommender>
   K8s Misconfigurations - Popeye <playbook-reference/actions/scans>

.. toctree::
   :maxdepth: 4
   :caption: 🤖 AI Analysis
   :hidden:

   configuration/holmesgpt/main-features
   configuration/holmesgpt/getting-started
   HolmesGPT Docs <configuration/holmesgpt/holmesgpt-docs>

.. toctree::
   :maxdepth: 4
   :caption: 💼 Robusta Pro Features
   :hidden:

   configuration/exporting/robusta-pro-features
   setup-robusta/alertsui
   configuration/exporting/send-alerts-api
   configuration/exporting/configuration-changes-api
   configuration/exporting/alert-export-api
   configuration/exporting/alert-statistics-api
   configuration/exporting/namespace-resources-api
   configuration/exporting/rbac-api

.. toctree::
   :maxdepth: 4
   :caption: ❓ Help
   :hidden:

   help
   contributing
   community-tutorials

Welcome to Robusta
====================

Robusta transforms basic Prometheus alerts into actionable insights with full Kubernetes context, and magical automation.

.. grid:: 1 1 1 2
    :margin: 0
    :padding: 0
    :gutter: 3

    .. grid-item::

        **How Robusta Improves Alerts:**

        * **Self-Healing** - Define auto-remediation rules for faster fixes
        * **Smart Grouping** - Reduce notification spam
        * **AI Investigation** - Kickstart alert investigation with AI
        * **Alert Enrichment** - Pod logs, events and more alongside alerts


        Connect to your existing Prometheus or install our all-in-one bundle (based on kube-prometheus-stack). Need to go beyond Kubernetes? `Try Robusta Pro <https://home.robusta.dev>`_.

    .. grid-item::

        .. image:: /images/prometheus-alert-with-robusta.png
            :width: 400px

Ready to get started?
---------------------

Join hundreds of teams already running Robusta in production.

.. button-ref:: ../setup-robusta/installation/index
    :color: primary
    :outline:

    Get Started →
