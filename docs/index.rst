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

   how-it-works/index
   how-it-works/architecture
   how-it-works/oss-vs-saas
   how-it-works/privacy-and-security
   how-it-works/coverage
   how-it-works/usage-faq

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
   🆕 Notification Grouping <configuration/notification-grouping>
   🪄 AI Analysis - HolmesGPT <configuration/ai-analysis>
   Cost Savings - KRR <configuration/resource-recommender>
   K8s Misconfigurations - Popeye <configuration/cluster-misconfigurations>
   configuration/configuring-sinks
   🔔 Sinks Reference <configuration/sinks/index>
   configuration/alertmanager-integration/index
   configuration/exporting/exporting-data
   configuration/additional-settings

.. toctree::
   :maxdepth: 4
   :caption: 🔔 Notifications & Routing
   :hidden:

   notification-routing/configuring-sinks
   🆕 Notification Grouping <notification-routing/notification-grouping>
   notification-routing/routing-by-namespace
   notification-routing/routing-by-type
   notification-routing/routing-exclusion
   notification-routing/routing-silencing

.. toctree::
   :maxdepth: 4
   :caption: 🎨 Playbooks
   :hidden:

   playbook-reference/index

.. toctree::
   :maxdepth: 4
   :caption: 🎓 Tutorials
   :hidden:

   tutorials/index

.. toctree::
   :maxdepth: 4
   :caption: Help
   :hidden:

   help

Better Prometheus Alerts (and more) for Kubernetes
=====================================================

.. grid:: 1 1 2 2
    :margin: 0
    :padding: 0

    .. grid-item::

        Robusta extends Prometheus/VictoriaMetrics/Coralogix (and more) with features like:

        * :doc:`Smart Grouping <configuration/notification-grouping>` - reduce notification spam with Slack threads 🧵
        * :ref:`AI Investigation <AI Analysis>` - Kickstart your alert investigations with AI (optional)
        * :ref:`Alert Enrichment <Automatically Investigate a Prometheus Alert>` - see pods log and other data alongside your alerts
        * :ref:`Self-Healing <Remediate Prometheus Alerts>` - define auto-remediation rules for faster fixes
        * :ref:`Advanced Routing <Notification Routing>` by team, namespace, k8s metadata and more
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
