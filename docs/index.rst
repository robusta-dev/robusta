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

   configuration/overview
   Connecting sinks <configuration/sinks-configuration>
   configuration/defining-playbooks
   configuration/additional-playbooks
   Re-using common settings <configuration/global-config>
   Handling Secrets <configuration/configuration-secrets>
   How playbooks work <configuration/flow-control>
   configuration/alert-manager
   configuration/embedded-prometheus
   Robusta CLI <configuration/robusta-cli>
   configuration/trigger-action-binding
   tutorials/prometheus-enrichment
   coverage
   Robusta UI Triggers <how-it-works/robusta-ui-triggers>


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

Robusta is a Kubernetes-native observability platform. It is commonly used as an extension to Prometheus, or a standalone monitoring solution.

Robusta gathers Kubernetes-specific data when alerts fire, as well as tracking CrashLoopBackOffs, Job failures, and other native Kubernetes events.

Finally, it routes notifications to Slack, MSTeams, PagerDuty (and more) via a unified event bus. In short, better notifications, unified routing.

Capabilities
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. grid:: 2
    :margin: 0
    :padding: 0

    .. grid-item::
        :columns: 6

        * Correlate Prometheus alerts with pod logs
        * Attach missing information to your alerts (e.g. ``kubectl get events``)
        * Notify on Kubernetes-native errors, like Job failure
        * Understand *why* alerts fired, with automated community runbooks
        * Remediate alerts by automatically running commands

        ...and more!

        .. button-ref:: get-started/index
            :color: primary
            :outline:

            Get Started →


    .. grid-item::
       :columns: 6

       .. image:: /images/architecture-overview.png
          :align: center
