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

   user-guide/overview
   user-guide/defining-playbook
   user-guide/global-config
   user-guide/sink-configuration
   user-guide/additional-playbooks
   user-guide/Secrets <configuration-secrets>
   user-guide/alert-manager
   user-guide/embeded-prometheus
   Upgrade & Uninstall <upgrade>


..
   tutorials/alert-correlation

.. toctree::
   :maxdepth: 4
   :caption: Architecture
   :hidden:
    
   Overview <home>
   oss-vs-saas
   Robusta UI Triggers <advanced/robusta-ui-triggers>
   Privacy & Security <advanced/privacy-and-security>



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
Robusta is an open source platform for Kubernetes monitoring and runbook automation. It can be installed as full monitoring stack or an add-on for Prometheus and other tools.

Robusta watches your cluster, identifies problems, and gathers observability data about the cause. It also support writing automatic remediations.

.. button-ref:: gettingstarted-index
    :color: primary
    :outline:

    Get Started →

Learn about Robusta
^^^^^^^^^^^^^^^^^^

.. grid:: 1 1 2 4
    :gutter: 3

    .. grid-item-card:: :octicon:`info;1em;` Architecture
        :class-card: sd-bg-light sd-bg-text-light
        :link: /developer-guide/actions/index
        :link-type: doc

        Technical details of how everything works

    .. grid-item-card:: :octicon:`book;1em;` Track Kubernetes Changes
        :class-card: sd-bg-light sd-bg-text-light
        :link: /using-robusta/trackchanges
        :link-type: doc

        Get notified when something changes in your cluster

    .. grid-item-card:: :octicon:`info;1em;` Supported Sinks
        :class-card: sd-bg-light sd-bg-text-light
        :link: /catalog/sinks/index
        :link-type: doc

        See all the integrations you can send data to 
