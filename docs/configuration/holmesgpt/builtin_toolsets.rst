
Builtin Toolsets
================

.. toctree::
   :hidden:
   :maxdepth: 1

   toolsets/argocd
   toolsets/aws
   toolsets/confluence
   toolsets/docker
   toolsets/grafanaloki
   toolsets/grafanatempo
   toolsets/helm
   toolsets/internet
   toolsets/kafka
   toolsets/kubernetes
   toolsets/opensearch
   toolsets/robusta
   toolsets/slab

Holmes allows you to define and configure integrations (toolsets) that fetch data from external sources. This data
will be automatically used in investigations when relevant.

You can :doc:`write your own toolset <custom_toolsets>` or use the default Holmes toolsets listed below.


Builtin toolsets
^^^^^^^^^^^^^^^^
Holmes comes with a set of builtin toolsets. Some of these toolsets are enabled by default, such as toolsets
to read Kubernetes resources and fetch logs. Some builtin toolsets are disabled by default and can be enabled
by the user by providing credentials or API keys to external systems.

.. grid:: 1 1 2 3
    :gutter: 3

    .. grid-item-card:: :octicon:`cpu;1em;` ArgoCD
        :class-card: sd-bg-light sd-bg-text-light
        :link: toolsets/argocd
        :link-type: doc

    .. grid-item-card:: :octicon:`cpu;1em;` AWS
        :class-card: sd-bg-light sd-bg-text-light
        :link: toolsets/aws
        :link-type: doc

    .. grid-item-card:: :octicon:`cpu;1em;` Confluence
        :class-card: sd-bg-light sd-bg-text-light
        :link: toolsets/confluence
        :link-type: doc

    .. grid-item-card:: :octicon:`cpu;1em;` Docker
        :class-card: sd-bg-light sd-bg-text-light
        :link: toolsets/docker
        :link-type: doc

    .. grid-item-card:: :octicon:`cpu;1em;` Grafana
        :class-card: sd-bg-light sd-bg-text-light
        :link: toolsets/grafana
        :link-type: doc

    .. grid-item-card:: :octicon:`cpu;1em;` Helm
        :class-card: sd-bg-light sd-bg-text-light
        :link: toolsets/helm
        :link-type: doc

    .. grid-item-card:: :octicon:`cpu;1em;` Internet
        :class-card: sd-bg-light sd-bg-text-light
        :link: toolsets/internet
        :link-type: doc

    .. grid-item-card:: :octicon:`cpu;1em;` Kafka
        :class-card: sd-bg-light sd-bg-text-light
        :link: toolsets/kafka
        :link-type: doc

    .. grid-item-card:: :octicon:`cpu;1em;` Kubernetes
        :class-card: sd-bg-light sd-bg-text-light
        :link: toolsets/kubernetes
        :link-type: doc
    .. grid-item-card:: :octicon:`cpu;1em;` OpenSearch
        :class-card: sd-bg-light sd-bg-text-light
        :link: toolsets/opensearch
        :link-type: doc

    .. grid-item-card:: :octicon:`cpu;1em;` Robusta
        :class-card: sd-bg-light sd-bg-text-light
        :link: toolsets/robusta
        :link-type: doc

    .. grid-item-card:: :octicon:`cpu;1em;` Slab
        :class-card: sd-bg-light sd-bg-text-light
        :link: toolsets/slab
        :link-type: doc
