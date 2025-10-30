:tocdepth: 2

.. _install-all-in-one:

Install Robusta + Prometheus
####################################
*Estimated time: 5 minutes*

Setup Kubernetes monitoring from scratch. Install Robusta, Prometheus, and Grafana on Kubernetes using Helm. This is the recommended setup for users that are setting up Kubernetes monitoring from scratch.

Prerequisites
---------------------

* A :ref:`supported Kubernetes cluster <Supported Clusters>`
* Helm

.. jinja::
   :inline-ctx: { "gen_config_flags": "--enable-prometheus-stack" }
   :header_update_levels:
   :file: setup-robusta/installation/_generate_config.jinja

.. include:: ./_helm_install_with_prometheus.inc.rst

Next Steps
---------------------------------

:doc:`Investigate your alerts with AI </configuration/holmesgpt/main-features>`
