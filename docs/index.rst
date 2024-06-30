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
   🆕 AI Analysis <configuration/ai-analysis>
   configuration/configuring-sinks
   🔔 Sinks Reference <configuration/sinks/index>
   configuration/alertmanager-integration/index
   configuration/additional-settings


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

        What Does Robusta Add to Prometheus?
        -------------------------------------

        Robusta extends Prometheus/VictoriaMetrics/Coralogix (and more) with features like:

        * :doc:`Smart Grouping <configuration/notification-grouping>` - reduce notification spam with Slack threads 🧵
        * :ref:`AI Investigation <AI Analysis>` - Kickstart your alert investigations with AI (optional)
        * :ref:`Alert Enrichment <Automatically Investigate a Prometheus Alert>` - see pods logs and other data alongside your alerts
        * :ref:`Self-Healing <Remediate Prometheus Alerts>` - define auto-remediation rules for faster fixes
        * :ref:`K8s-Native Alert Routing <Notification Routing>` by team, namespace, k8s metadata and more
        * :ref:`Problem-Detection without PromQL <Triggers Reference>` - alert on OOMKills, failing Jobs, etc
        * :ref:`Change Tracking <Track Kubernetes Changes>` for Kubernetes Resources to correlate alerts and rollouts
        * :ref:`Auto-Resolve <Jira>` - send alerts, later update them as resolved (e.g. in Jira)
        * :ref:`Dozens of Integrations <Integrations Overview>` - Slack, Teams, Jira, and more

        Bring your own Prometheus or install our :ref:`preconfigured bundle <Embedded Prometheus Stack>`.

    .. grid-item::

        .. md-tab-set::

            .. md-tab-item:: Alert Enrichment

               .. image:: /images/prometheus-alert-with-robusta.png
                   :width: 800px

            .. md-tab-item:: Track OOMKills

               .. image:: /images/oomkillpod.png
                   :width: 800px

            .. md-tab-item:: Stuck Job

               .. image:: /images/struckjob.png
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
