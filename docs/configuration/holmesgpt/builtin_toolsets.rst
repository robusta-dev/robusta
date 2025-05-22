
Builtin Toolsets
================

.. toctree::
   :hidden:
   :maxdepth: 1

   toolsets/argocd
   toolsets/aws
   toolsets/confluence
   toolsets/coralogix_logs
   toolsets/datetime
   toolsets/docker
   toolsets/grafanaloki
   toolsets/grafanatempo
   toolsets/helm
   toolsets/internet
   toolsets/kafka
   toolsets/kubernetes
   toolsets/opensearch_logs
   toolsets/opensearch_status
   toolsets/prometheus
   toolsets/rabbitmq
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

    .. grid-item-card:: :octicon:`cpu;1em;` Coralogix logs
        :class-card: sd-bg-light sd-bg-text-light
        :link: toolsets/coralogix_logs
        :link-type: doc

    .. grid-item-card:: :octicon:`cpu;1em;` Datetime
        :class-card: sd-bg-light sd-bg-text-light
        :link: toolsets/datetime
        :link-type: doc

    .. grid-item-card:: :octicon:`cpu;1em;` Docker
        :class-card: sd-bg-light sd-bg-text-light
        :link: toolsets/docker
        :link-type: doc

    .. grid-item-card:: :octicon:`cpu;1em;` Grafana Loki
        :class-card: sd-bg-light sd-bg-text-light
        :link: toolsets/grafanaloki
        :link-type: doc

    .. grid-item-card:: :octicon:`cpu;1em;` Grafana Tempo
        :class-card: sd-bg-light sd-bg-text-light
        :link: toolsets/grafanatempo
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

    .. grid-item-card:: :octicon:`cpu;1em;` OpenSearch logs
        :class-card: sd-bg-light sd-bg-text-light
        :link: toolsets/opensearch_logs
        :link-type: doc

    .. grid-item-card:: :octicon:`cpu;1em;` OpenSearch status
        :class-card: sd-bg-light sd-bg-text-light
        :link: toolsets/opensearch_status
        :link-type: doc

    .. grid-item-card:: :octicon:`cpu;1em;` Prometheus
        :class-card: sd-bg-light sd-bg-text-light
        :link: toolsets/prometheus
        :link-type: doc

    .. grid-item-card:: :octicon:`cpu;1em;` RabbitMQ
        :class-card: sd-bg-light sd-bg-text-light
        :link: toolsets/rabbitmq
        :link-type: doc

    .. grid-item-card:: :octicon:`cpu;1em;` Robusta
        :class-card: sd-bg-light sd-bg-text-light
        :link: toolsets/robusta
        :link-type: doc

    .. grid-item-card:: :octicon:`cpu;1em;` Slab
        :class-card: sd-bg-light sd-bg-text-light
        :link: toolsets/slab
        :link-type: doc
