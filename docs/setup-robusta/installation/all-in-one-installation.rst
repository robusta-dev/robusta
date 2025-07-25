:tocdepth: 2

.. _install-all-in-one:

Monitor Kubernetes from Scratch
####################################
*Estimated time: 5 minutes*

Setup Kubernetes monitoring from scratch. Install Robusta, Prometheus, and Grafana on Kubernetes using Helm. This is the recommended way to monitor your cluster, with an all-in-one package.

Prerequisites
---------------------

* A :ref:`supported Kubernetes cluster <Supported Clusters>`
* Helm

.. jinja::
   :inline-ctx: { "gen_config_flags": "--enable-prometheus-stack" }
   :header_update_levels:
   :file: setup-robusta/installation/_generate_config.jinja

.. include:: ./_helm_install_with_prometheus.inc.rst

.. include:: ./_see_robusta_in_action.rst

Next Steps
---------------------------------

:ref:`See how Robusta improves Prometheus <builtin-alert-enrichment>`.
