:tocdepth: 2
:globaltoc_collapse: false

.. _install-barebones:

Barebones Installation
####################################

*Estimated time: 5 minutes*

Install Robusta standalone, without integrating Prometheus. See Robusta's native capabilities.

.. warning::

   Most people should install with Prometheus **instead** of this tutorial.

   Robusta is useful standalone, but Prometheus makes it even better!

Prerequisites
---------------------

* A :ref:`supported Kubernetes cluster <Supported Kubernetes Clusters>`
* Helm

.. include:: ../_questions.rst

.. jinja::
   :inline-ctx: {"gen_config_flags": "--no-enable-prometheus-stack"}
   :header_update_levels:
   :file: setup-robusta/installation/_generate_config.jinja

.. include:: ./_helm_install.rst

.. include:: ./_see_robusta_in_action.rst


Next Steps
---------------------------------

* :ref:`Track Failed Kubernetes Jobs`
* :ref:`View more tutorials<Tutorials>`