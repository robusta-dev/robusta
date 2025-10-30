:tocdepth: 2

.. _install-barebones:

Install Robusta
###############

Prerequisites
---------------------

* A :ref:`supported Kubernetes cluster <Supported Clusters>`
* Helm

.. jinja::
   :inline-ctx: {"gen_config_flags": "--no-enable-prometheus-stack"}
   :header_update_levels:
   :file: setup-robusta/installation/_generate_config.jinja

.. include:: ./_helm_install_no_prometheus.inc.rst


Next Steps
---------------------------------

1. :doc:`Send alerts to Robusta </configuration/index>`
2. :doc:`Investigate your alerts with AI </configuration/holmesgpt/main-features>`