:hide-toc:

.. toctree::
   :maxdepth: 1
   :caption: 📖 Overview
   :hidden:

   self
   how-it-works/architecture
   how-it-works/oss-vs-saas
   how-it-works/coverage
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
   Nagios <configuration/alertmanager-integration/nagios>
   SolarWinds <configuration/alertmanager-integration/solarwinds>
   Custom Webhooks <configuration/exporting/custom-webhooks>


.. toctree::
   :maxdepth: 4
   :caption: 🔔 Notifications & Routing
   :hidden:

   Overview <notification-routing/index>
   notification-routing/configuring-sinks
   📧 Sink Reference <configuration/sinks/index>
   Routing (Scopes) <notification-routing/routing-with-scopes>
   Grouping (Slack Threads) <notification-routing/notification-grouping>
   notification-routing/routing-by-time
   notification-routing/routing-silencing
   notification-routing/notification-routing-examples

.. toctree::
   :maxdepth: 4
   :caption: ⚙️ Automation
   :hidden:

   playbook-reference/index
   configuration/alertmanager-integration/alert-custom-prometheus
   Cost Savings - KRR <configuration/resource-recommender>
   K8s Misconfigurations - Popeye <configuration/cluster-misconfigurations>

.. toctree::
   :maxdepth: 4
   :caption: 💼 Robusta Pro Features
   :hidden:

   configuration/exporting/robusta-pro-features
   configuration/holmesgpt/index
   configuration/exporting/exporting-data
   configuration/alertmanager-integration/troubleshooting-alertmanager

.. toctree::
   :maxdepth: 4
   :caption: ❓ Help
   :hidden:

   help
   contributing
   community-tutorials

Welcome to Robusta
====================

.. grid:: 1 1 1 2
    :margin: 0
    :padding: 0
    :gutter: 3

    .. grid-item::

        Robusta OSS enriches Prometheus alerts with Kubernetes context.

        When Prometheus alerts fire, Robusta automatically adds pod logs, events, and metrics. Robusta Pro adds web UI, AI analysis, and support for non-Kubernetes monitoring systems.

        .. raw:: html

           <br>

        **What happens when an alert fires:**

        * **Auto-investigate** - Logs, events, and metrics attached
        * **AI analysis** - Root causes and fixes suggested  
        * **Smart routing** - Right team, right channel
        * **Self-healing** - Automatic remediation rules
        * **Change tracking** - Correlate alerts with deployments

        .. raw:: html

           <br>

        **Works with your existing setup**

        Connect to your existing Prometheus or install our all-in-one bundle (based on kube-prometheus-stack).

    .. grid-item::

        .. md-tab-set::

            .. md-tab-item:: Alert Enrichment

               .. image:: /images/prometheus-alert-with-robusta.png
                   :width: 800px

            .. md-tab-item:: AI Investigation

               .. image:: /images/ai-analysis.png
                   :width: 800px

            .. md-tab-item:: Kubernetes Problems

               .. image:: /images/oomkillpod.png
                   :width: 800px

            .. md-tab-item:: JIRA Integration

               .. image:: /images/jira_example.png
                   :width: 800px

Ready to get started?
---------------------

Join hundreds of teams already running Robusta in production.

.. button-ref:: ../setup-robusta/installation/index
    :color: primary
    :outline:

    Get Started →
