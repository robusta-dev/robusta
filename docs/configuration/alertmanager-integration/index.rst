:hide-toc:



Integrating with Prometheus
================================
.. toctree::
   :hidden:
   :maxdepth: 1

   kube-prometheus-stack
   alert-manager
   outofcluster-prometheus
   azure-managed-prometheus
   victoria-metrics
   grafana-alert-manager
   embedded-prometheus


Robusta can :ref:`enhance Prometheus alerts<Enhanced Prometheus Alerts>`. Instructions below.

If you installed Robusta's :ref:`Embedded Prometheus Stack`, no setup necessary.


Setup Instructions
^^^^^^^^^^^^^^^^^^

.. grid:: 1 1 2 3
    :gutter: 3

    .. grid-item-card:: :octicon:`book;1em;` kube-prometheus-stack
        :class-card: sd-bg-light sd-bg-text-light
        :link: kube-prometheus-stack
        :link-type: doc

        In-cluster Prometheus, using Prometheus Operator

    .. grid-item-card:: :octicon:`book;1em;` In-cluster Prometheus
        :class-card: sd-bg-light sd-bg-text-light
        :link: alert-manager
        :link-type: doc

        In-cluster Prometheus, not kube-prometheus-stack

    .. grid-item-card:: :octicon:`book;1em;` Out of cluster Prometheus
        :class-card: sd-bg-light sd-bg-text-light
        :link: outofcluster-prometheus
        :link-type: doc

        Prometheus in a separate cluster from Robusta

    .. grid-item-card:: :octicon:`book;1em;` Azure Managed Prometheus
        :class-card: sd-bg-light sd-bg-text-light
        :link: azure-managed-prometheus
        :link-type: doc

        Azure's Prometheus offering

    .. grid-item-card:: :octicon:`book;1em;` Victoria Metrics
        :class-card: sd-bg-light sd-bg-text-light
        :link: victoria-metrics
        :link-type: doc

        Prometheus Compatible, Robusta Compatible

    .. grid-item-card:: :octicon:`book;1em;` Grafana AlertManager
        :class-card: sd-bg-light sd-bg-text-light
        :link: grafana-alert-manager
        :link-type: doc

        For anyone using Grafana alerts

    .. grid-item-card:: :octicon:`book;1em;` Embedded Prometheus
        :class-card: sd-bg-light sd-bg-text-light
        :link: embedded-prometheus
        :link-type: doc

        Robusta's embedded Prometheus Stack
