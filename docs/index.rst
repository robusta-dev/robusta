:hide-navigation:
:hide-toc:

.. toctree::
   :maxdepth: 4
   :caption: Home
   :hidden:

   self

.. toctree::
   :maxdepth: 4
   :caption: How it works
   :hidden:

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
   :caption: 🔌 Integrations
   :hidden:

   configuration/index
   🪄 AI Analysis - HolmesGPT <configuration/holmesgpt/index>
   🔔 Sinks <configuration/sinks/index>
   🔥 Prometheus/AlertManager <configuration/alertmanager-integration/index>
   Cost Savings - KRR <configuration/resource-recommender>
   K8s Misconfigurations - Popeye <configuration/cluster-misconfigurations>
   configuration/exporting/exporting-data

.. toctree::
   :maxdepth: 4
   :caption: 🔔 Notifications & Routing
   :hidden:

   notification-routing/configuring-sinks
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

.. toctree::
   :maxdepth: 4
   :caption: Help
   :hidden:

   help
   contributing
   community-tutorials

Better Prometheus Alerts (and more) for Kubernetes
=====================================================

.. grid:: 1 1 2 2
    :margin: 0
    :padding: 0

    .. grid-item::

        Robusta extends Prometheus/VictoriaMetrics/Coralogix (and more) with features like:

        * :doc:`Smart Grouping <notification-routing/notification-grouping>` - reduce notification spam with Slack threads 🧵
        * :ref:`AI Investigation <AI Analysis>` - Kickstart your alert investigations with AI (optional)
        * :ref:`Alert Enrichment <Automatically Investigate a Prometheus Alert>` - see pods log and other data alongside your alerts
        * :ref:`Self-Healing <Automatic Remediation>` - define auto-remediation rules for faster fixes
        * :ref:`Advanced Routing <Defining Sinks>` by team, namespace, k8s metadata and more
        * :ref:`K8s Problem-Detection <Triggers Reference>` - alert on OOMKills or failing Jobs without PromQL
        * :ref:`Change Tracking <Track Kubernetes Changes>` - correlate alerts and Kubernetes rollouts
        * :ref:`Auto-Resolve <Jira>` - send alerts, resolve them when updated (e.g. in Jira)
        * :ref:`Dozens of Integrations <Integrations Overview>` - Slack, Teams, Jira, and more

        Bring your own Prometheus or install our :ref:`preconfigured bundle <Embedded Prometheus Stack>`.

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

Who uses Robusta?
-------------------------------------

Robusta is used in production by hundreds of teams, from cloud-native pioneers to the Fortune 500.

.. button-ref:: ../setup-robusta/installation/index
    :color: primary
    :outline:

    Get Started →
