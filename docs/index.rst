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
   
   Overview <gettingstarted-index>
   Install with Helm <installation>
   Install with ArgoCD <tutorials/argocd-installation>
   tutorials/add-more-clusters
   using-robusta/trackchanges
   using-robusta/enrich-alerts
   Remediate Alerts <using-robusta/remediatealerts>
   Route Alerts <using-robusta/routealerts>
   More tutorials <tutorials/blogs-videos>
   

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
   Upgrade & Uninstall <upgrade>
   configuration/embedded-prometheus



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

   catalog/overview
   catalog/triggers/index
   catalog/actions/index
   catalog/sinks/index

.. toctree::
   :maxdepth: 4
   :caption: Extending
   :hidden:

   tutorials/overview
   tutorials/my-first-custom-action
   Write Python automations <developer-guide/actions/index>
   Modify Robusta core <developer-guide/platform/index>
   Docs Contributions <developer-guide/platform/docs-contributions>

.. toctree::
   :maxdepth: 4
   :caption: Help
   :hidden:

   help



Welcome to Robusta Docs
===================
Robusta is an open source platform for Kubernetes monitoring and runbook automation. It can be installed as a full monitoring stack or an add-on for Prometheus and other tools.

Robusta watches your cluster, identifies problems, and gathers observability data about the cause. It also supports automatic remediation.

.. button-ref:: gettingstarted-index
    :color: primary
    :outline:

    Get Started →

Learn about Robusta
^^^^^^^^^^^^^^^^^^

.. grid:: 1 1 2 4
    :gutter: 3

    .. grid-item-card:: :octicon:`info;1em;` Architecture
        :link: architecture/index
        :link-type: doc

        Technical details of how everything works

    .. grid-item-card:: :octicon:`book;1em;` Track Kubernetes Changes
        :link: /using-robusta/trackchanges
        :link-type: doc

        Get notified when something changes in your cluster

    .. grid-item-card:: :octicon:`info;1em;` Supported Sinks
        :link: /catalog/sinks/index
        :link-type: doc

        See all the integrations you can send data to 
