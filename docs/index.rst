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

   Overview <how-it-works/index>
   Components <how-it-works/components>
   how-it-works/oss-vs-saas
   Privacy & Security <how-it-works/privacy-and-security>

.. toctree::
   :maxdepth: 4
   :caption: Get Started
   :hidden:
   
   Overview <get-started/index>

.. toctree::
   :maxdepth: 4
   :caption: Installation
   :hidden:

   setup-robusta/index

.. toctree::
   :maxdepth: 4
   :caption: Reference
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
   :caption: Examples
   :hidden:

   advanced-tutorials/index


.. toctree::
   :maxdepth: 4
   :caption: Automation
   :hidden:

   automation/overview
   automation/automation-basics
   automation/triggers/index
   automation/actions/index
   automation/sinks/index
   popular-automations/index

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

Robusta helps you get more out of Prometheus on Kubernetes. To be precise, some people use Robusta for observability or runbook automation without Prometheus, but they're best together.

.. grid:: 2
    :margin: 0
    :padding: 0

    .. grid-item::
        :columns: 6

        Robusta extends Prometheus with full Kubernetes observability, letting you:

        * Correlate Prometheus alerts with pod logs
        * Attach APIServer information (e.g. ``kubectl get events``) to your alerts
        * See which alerts fired on a Deployment or Node
        * Understand *why* alerts occurred and what led to them firing
        * Perform automatic remediations

        ...and more!


    .. grid-item::
       :columns: 6

       .. image:: /images/architecture-overview.png
          :align: center


.. button-ref:: get-started/index
    :color: primary
    :outline:

    Get Started →
