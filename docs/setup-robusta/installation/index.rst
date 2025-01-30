:hide-toc:

:hide-footer:

.. _install:

Installation Guides
====================

.. toctree::
   :maxdepth: 1
   :hidden:

   all-in-one-installation
   extend-prometheus-installation
   standalone-installation
   dev-setup
   


.. grid:: 1 1 2 2
    :gutter: 2

    .. grid-item-card:: Monitor Kubernetes from Scratch
        :class-card: sd-bg-text-light
        :link: all-in-one-installation
        :link-type: doc

    .. grid-item-card:: Integrate with Existing Prometheus
        :class-card: sd-bg-light sd-bg-text-light
        :link: extend-prometheus-installation
        :link-type: doc

    .. grid-item::
        .. raw:: html

           <span style="color: #808080;">Five minute setup. Great default alerts. Powered by Prometheus and Robusta.</span>

    .. grid-item::
        .. raw:: html

           <span style="color: #808080;">Make your existing alerts better. Attach pod logs. Automatic alert insights.</span>

Don't want Prometheus? Use :ref:`Robusta without Prometheus <install-barebones>`.


Already installed Robusta? See what you can do with it.
-------------------------------------------------------------

`Route alerts to different teams based on namespace, alertname, and more <https://docs.robusta.dev/master/tutorials/index.html#notification-routing>`_

`Enhance Prometheus alerts with Robusta <https://docs.robusta.dev/master/tutorials/alert-builtin-enrichment.html>`_

`Define new Prometheus alerts <https://docs.robusta.dev/master/tutorials/alert-custom-prometheus.html>`_

`Configure auto-remediate for Prometheus alerts <https://docs.robusta.dev/master/tutorials/alert-remediation.html>`_

`Track Kubernetes errors and changes using simple YAML <https://docs.robusta.dev/master/tutorials/index.html#custom-alerts-and-playbooks>`_
