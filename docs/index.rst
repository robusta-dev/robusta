:hide-toc:

.. toctree::
   :maxdepth: 1
   :caption: Overview
   :hidden:

   self
   how-it-works/architecture
   how-it-works/oss-vs-saas
   how-it-works/usage-faq

.. toctree::
   :maxdepth: 4
   :caption: Installation
   :hidden:

   setup-robusta/index

.. toctree::
   :maxdepth: 4
   :caption: AI Analysis
   :hidden:

   configuration/holmesgpt/main-features
   configuration/holmesgpt/getting-started
   HolmesGPT Docs <configuration/holmesgpt/holmesgpt-docs>

.. toctree::
   :maxdepth: 4
   :caption: Send Alerts
   :hidden:

   Overview <configuration/index>
   AlertManager - external <configuration/alertmanager-integration/outofcluster-prometheus>
   AlertManager - in-cluster <configuration/alertmanager-integration/alert-manager>
   AWS Managed Prometheus <configuration/alertmanager-integration/eks-managed-prometheus>
   Azure Managed Prometheus <configuration/alertmanager-integration/azure-managed-prometheus>
   Coralogix <configuration/alertmanager-integration/coralogix_managed_prometheus>
   Dynatrace <configuration/alertmanager-integration/dynatrace>
   Embedded Prometheus Stack <configuration/alertmanager-integration/embedded-prometheus>
   Google Managed Prometheus <configuration/alertmanager-integration/google-managed-prometheus>
   Grafana - Self-Hosted <configuration/alertmanager-integration/grafana-self-hosted>
   Grafana Cloud <configuration/alertmanager-integration/grafana-cloud>
   Nagios <configuration/alertmanager-integration/nagios>
   New Relic <configuration/alertmanager-integration/newrelic>
   PagerDuty <configuration/alertmanager-integration/pagerduty-alerting>
   SolarWinds <configuration/alertmanager-integration/solarwinds>
   VictoriaMetrics <configuration/alertmanager-integration/victoria-metrics>
   Customize Labels & Priorities <configuration/alertmanager-integration/customize-labels-priorities>
   Other - Custom Webhooks <configuration/exporting/custom-webhooks>

.. toctree::
   :maxdepth: 4
   :caption: Track Config Changes
   :hidden:

   track-changes/kubernetes-changes
   LaunchDarkly <configuration/alertmanager-integration/launchdarkly>

.. toctree::
   :maxdepth: 4
   :caption: Connect Metrics
   :hidden:

   General Settings <configuration/metric-providers>
   Prometheus - in-cluster <configuration/metric-providers-in-cluster>
   Prometheus - external <configuration/metric-providers-external>
   Azure Managed <configuration/metric-providers-azure>
   AWS Managed <configuration/metric-providers-aws>
   Google Managed <configuration/metric-providers-google>
   Coralogix <configuration/metric-providers-coralogix>
   VictoriaMetrics <configuration/metric-providers-victoria>
   Grafana Cloud (Mimir) <configuration/metric-providers-grafana-cloud>

.. toctree::
   :maxdepth: 4
   :caption: Notification Sinks
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
   :caption: Alert Routing
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
   :caption: Robusta Pro Features
   :hidden:

   configuration/exporting/robusta-pro-features
   setup-robusta/alertsui
   setup-robusta/crds
   configuration/exporting/send-alerts-api
   configuration/exporting/configuration-changes-api
   configuration/exporting/alert-export-api
   configuration/exporting/alert-statistics-api
   configuration/exporting/namespace-resources-api
   configuration/exporting/rbac-api

.. toctree::
   :maxdepth: 4
   :caption: Advanced - Playbooks
   :hidden:

   playbook-reference/index
   Playbook Notifications <playbook-reference/defining-playbooks/creating-notifications>
   Alert Enrichment <playbook-reference/builtin-alert-enrichment>
   Automatic Remediation <playbook-reference/automatic-remediation-examples/index>
   Silencer Playbooks <playbook-reference/defining-playbooks/silencer-playbooks>
   Triggers Reference <playbook-reference/triggers/index>
   Actions Reference <playbook-reference/actions/index>
   Log Based Alerting <playbook-reference/logs-triggers/index>
   K8s Change Notification <playbook-reference/kubernetes-examples/kubernetes-change-notifications>
   Cost Savings - KRR <configuration/resource-recommender>

.. toctree::
   :maxdepth: 4
   :caption: Help
   :hidden:

   help
   contributing
   community-tutorials

Welcome to Robusta
====================

Robusta is an SRE agent that transforms alerts into actionable insights using LLMs combined with a rules (playbooks) engine.

Robusta is available in open-source and commercial versions:

.. list-table::
   :widths: 30 35 35
   :header-rows: 1

   * - **Version**
     - **Cloud Environments**
     - **Alert Sources**
   * - `Robusta Open Source <https://github.com/robusta-dev/robusta>`_
     - Kubernetes
     - Prometheus
   * - `Robusta Pro <https://home.robusta.dev>`_
     - Kubernetes and non-Kubernetes environments
     - Prometheus, DataDog, NewRelic, and more

**Key Features:**

* **Smart Grouping** - Reduce notification spam
* **AI Investigation** - Find the root cause with AI
* **Alert Enrichment** - Correlate alerts with logs, k8s events, and more
* **Auto-Remediation** - Define self-healing rules for faster fixes

Ready to get started?
---------------------

Join hundreds of teams already running Robusta in production.

.. button-ref:: ../setup-robusta/installation/index
    :color: primary
    :outline:

    Get Started →
