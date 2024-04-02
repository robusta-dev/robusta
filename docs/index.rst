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
   configuration/configuring-sinks
   🔔 Sinks Reference <configuration/sinks/index>
   📈 Prometheus & Metrics <configuration/alertmanager-integration/index>
   ⚠️  AlertManager <configuration/alertmanager-integration/integrate-alertmanager>
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

Welcome to the Robusta Docs
===============================

Robusta is an open source observability tool for Kubernetes, which extends Prometheus. Using automation rules, Robusta automatically fetches the data you need to investigate, and attaches it to your alerts.

.. grid:: 1 1 2 2
    :margin: 0
    :padding: 0

    .. grid-item::

        **Examples**

        * When alerts fire on Pods, fetch Pod logs
        * When Jobs fail, show data from the last run
        * When Pods are Pending, see why (``kubectl get events``)
        * When common alerts in ``kube-prometheus-stack`` fire, suggest fixes
        * Optionally send alerts to ChatGPT for analysis (disabled by default)

        **More Features**

        * Batteries included. No need to define alerts or automations. (We regularly test our alerts on GKE, EKS, AKS, and RKE to fine-tune.)
        * Route alerts by namespace, team, and severity
        * Not just Prometheus. Send notifications for rollouts/changes too
        * Remediate alerts with custom commands
        * :ref:`Many integrations <Sinks Reference>`, including Slack, MSTeams, OpsGenie, PagerDuty, and JIRA

    .. grid-item::

        .. md-tab-set::

            .. md-tab-item:: Crashing Pod

               .. image:: /images/prometheus-alert-with-robusta.png
                   :width: 800px

            .. md-tab-item:: OOMKill

               .. image:: /images/oomkillpod.png
                   :width: 800px

            .. md-tab-item:: Stuck Job

               .. image:: /images/struckjob.png
                   :width: 800px

            .. md-tab-item:: JIRA Integration

               .. image:: /images/jira_example.png
                   :width: 800px

Robusta is used in production by hundreds of teams. It monitors infrastructure for Fortune 500 companies, MSPs, and startups.

It can install everything you need to monitor Kubernetes from scratch, or it can be added to an existing Prometheus.

.. button-ref:: ../setup-robusta/installation/index
    :color: primary
    :outline:

    Get Started →
