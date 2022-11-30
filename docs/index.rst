:hide-navigation:
:hide-toc:


.. toctree::
   :maxdepth: 4
   :caption: Home
   :hidden:

   self


.. toctree::
   :maxdepth: 4
   :caption: Getting Started
   :hidden:
   
   Overview <getting-started/index>
   Install with Helm <getting-started/installation>
   Install with ArgoCD <getting-started/argocd-installation>
   getting-started/add-more-clusters
   getting-started/trackchanges
   getting-started/enrich-alerts
   Remediate Alerts <getting-started/remediatealerts>
   Route Alerts <getting-started/routealerts>
   More tutorials <getting-started/more-tutorials>
   

.. toctree::
   :maxdepth: 4
   :caption: Configuration
   :hidden:

   configuration/overview
   configuration/global-config
   configuration/defining-playbooks
   configuration/sinks-configuration
   configuration/additional-playbooks
   Secrets <configuration/configuration-secrets>
   configuration/alert-manager
   Upgrade & Uninstall <configuration/upgrade>
   configuration/embedded-prometheus
   Robusta CLI <configuration/robusta-cli>
   configuration/flow-control
   configuration/trigger-action-binding
   tutorials/prometheus-enrichment
   coverage




..
   tutorials/alert-correlation

.. toctree::
   :maxdepth: 4
   :caption: Architecture
   :hidden:
    
   Overview <architecture/index>
   Components <architecture/components>
   architecture/oss-vs-saas
   Robusta UI Triggers <architecture/robusta-ui-triggers>
   Privacy & Security <architecture/privacy-and-security>



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



Welcome to Robusta Docs
=============================
Robusta is an open source platform for Kubernetes monitoring and runbook automation. It can be installed as a full monitoring stack or an add-on for Prometheus and other tools. Robusta watches your cluster, identifies problems, and gathers observability data about the cause. It also supports automatic remediation.

.. button-ref:: getting-started/index
    :color: primary
    :outline:

    Get Started →

Learn about Robusta
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. grid:: 1 1 2 4
    :gutter: 3

    .. grid-item-card:: Architecture
        :link: architecture/index
        :link-type: doc

        Technical details of how everything works

    .. grid-item-card:: Track Changes
        :link: /getting-started/trackchanges
        :link-type: doc

        Get notified when something changes in your cluster

    .. grid-item-card:: Supported Sinks
        :link: /automation/sinks/index
        :link-type: doc

        See all the integrations you can send data to 
