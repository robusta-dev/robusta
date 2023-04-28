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
   :hidden:

   quick-start

.. toctree::
   :maxdepth: 4
   :caption: Installation
   :hidden:

   setup-robusta/index

.. toctree::
   :maxdepth: 4
   :caption: Configuration
   :hidden:

   configuration/index
   configuration/sending-notifications
   configuration/sinks/index
   configuration/configuration-secrets
   configuration/alert-manager
   configuration/embedded-prometheus
   configuration/additional-settings
   configuration/defining-playbooks/index

.. toctree::
   :maxdepth: 4
   :caption: Tutorials
   :hidden:

   tutorials/index

.. toctree::
   :maxdepth: 4
   :caption: Extending
   :hidden:

   extending/overview
   Custom Python Actions <extending/actions/index>
   Modify Robusta core <extending/platform/index>
   Docs Contributions <extending/platform/docs-contributions>

.. toctree::
   :maxdepth: 4
   :caption: Help
   :hidden:

   help

Welcome to the Robusta Docs
=============================

Robusta is an observability and monitoring platform built for Kubernetes. It is commonly used as an extension to Prometheus, or standalone.


.. grid:: 2
    :margin: 0
    :padding: 0

    .. grid-item::
        :columns: 6

        **Why Use Robusta?**

        * Get better alerts - with automatic insights
        * Spend less time defining alerts - with opinionated defaults
        * Remove blind-spots - with direct APIServer monitoring
        * Reduce alert fatigue - with smart silencing and alert routing

        **Key Capabilities**

        * Correlate Prometheus alerts with pod logs, k8s events, and more
        * Notify on Kubernetes-native errors without PromQL
        * Alert analysis powered by `ChatGPT <https://github.com/robusta-dev/kubernetes-chatgpt-bot/>`_ and expert runbooks
        * Remediate alerts with automatic commands

    .. grid-item::
       :columns: 6

       .. image:: /images/architecture-overview.png
          :align: center

Robusta is used in production by hundreds of teams. It monitors infrastructure for the Hubble Space Telescope,
Fortune 500 companies, and startups of all sizes.

.. button-ref:: quick-start
    :color: primary
    :outline:

    Get Started →
