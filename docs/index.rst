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
   how-it-work/how-playbooks-work
   how-it-works/architecture
   how-it-works/oss-vs-saas
   how-it-works/flow-control
   Privacy & Security <how-it-works/privacy-and-security>
   how-it-works/usage-faq

.. toctree::
   :maxdepth: 4
   :hidden:

   get-started

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
   configuration/sinks/index
   configuration/defining-playbooks
   configuration/additional-playbooks
   Re-using common settings <configuration/global-config>
   Handling Secrets <configuration/configuration-secrets>
   configuration/alert-manager
   configuration/embedded-prometheus
   Robusta CLI <configuration/robusta-cli>
   configuration/trigger-action-binding
   tutorials/prometheus-enrichment
   coverage
   Robusta UI Triggers <how-it-works/robusta-ui-triggers>
   Two-way Interactivity <interactivity>

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
   extending/actions/my-first-custom-action
   Write Python automations <extending/actions/index>
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

        **Reasons to use Robusta:**

        * Get better alerts - with automatic insights
        * Spend less time defining alerts - with opinionated defaults
        * Remove blind-spots - with direct APIServer monitoring
        * Reduce alert fatigue - with smart silencing and routing

        **Things you can do with Robusta:**

        * Correlate Prometheus alerts with pod logs, Kubernetes events, and more
        * Notify on Kubernetes-native errors without PromQL
        * Analyze alerts with `ChatGPT <https://github.com/robusta-dev/kubernetes-chatgpt-bot/>`_ or expert runbooks
        * Remediate alerts with automatic commands

        .. button-ref:: get-started/index
            :color: primary
            :outline:

            Get Started →


    .. grid-item::
       :columns: 6

       .. image:: /images/architecture-overview.png
          :align: center
