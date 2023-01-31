:hide-toc:

Quick Install
===============

.. toctree::
   :maxdepth: 1
   :hidden:

   all-in-one-installation
   extend-prometheus-installation
   standalone-installation

Robusta can be installed three ways:

* :ref:`As an all-in-one package, including Robusta and Prometheus <Monitor Kubernetes from Scratch>`
* :ref:`As a standalone package, integrated with an existing Prometheus <Integrate with Existing Prometheus>`
* :ref:`As a standalone package, with no Prometheus connected <Barebones Installation>`

Choosing the right setup
********************************

**For clusters without an existing Prometheus**, use the all-in-one package.

**For clusters already monitored by Prometheus**, use the standalone and integrated package.

**For users who want to avoid using Prometheus**, use the standalone package. This will disable Prometheus-related features, but all other Robusta features will works.
