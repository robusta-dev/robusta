:hide-toc:

Managed Prometheus Reference Reference
==================

.. toctree::
   :hidden:
   :maxdepth: 1

   azure-managed-prometheus
   corlogix-managed-prometheus

Robusta enables seamless integration with several externally managed Prometheus instances.

Supported Externally Managed Prometheus Instances
^^^^^^^^^^^^^^^^^^^^^
Click a Prometheus for setup instructions.

.. grid:: 1 1 2 3
    :gutter: 3

    .. grid-item-card:: :octicon:`cpu;1em;` Azure
        :class-card: sd-bg-light sd-bg-text-light
        :link: azure-managed-prometheus
        :link-type: doc

    .. grid-item-card:: :octicon:`cpu;1em;` Corlogix
        :class-card: sd-bg-light sd-bg-text-light
        :link:  corlogix-managed-prometheus
        :link-type: doc

    .. grid-item-card:: :octicon:`cpu;1em;` :ref:`../alert-manager<Out-of-cluster Prometheus Installations>` GKE
        :class-card: sd-bg-light sd-bg-text-light

    .. grid-item-card:: :octicon:`cpu;1em;` EKS (Coming Soon)
        :class-card: sd-bg-light sd-bg-text-light

**Need support for a different type of managed Prometheus?** `Tell us and we'll add it. <https://github.com/robusta-dev/robusta/issues/new?assignees=&labels=&template=feature_request.md&title=Managed%Prometheus:>`_
