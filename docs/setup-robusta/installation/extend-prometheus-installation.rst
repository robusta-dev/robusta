:tocdepth: 2

.. _install-existing-prometheus:

Integrate with Existing Prometheus
####################################
*Estimated time: 5 minutes*

Install Robusta alongside an existing Prometheus. See what Robusta can do.

Prerequisites
---------------------

* A :ref:`supported Kubernetes cluster <Supported Clusters>`
* A Prometheus installation
* Helm

.. jinja::
   :inline-ctx: {"gen_config_flags": "--no-enable-prometheus-stack"}
   :header_update_levels:
   :file: setup-robusta/installation/_generate_config.jinja

.. include:: ./_helm_install_no_prometheus.inc.rst

.. include:: ./_see_robusta_in_action.rst

Next Steps
---------------------------------

Integrate Robusta with AlertManager:

* :ref:`Follow a guide to integrate AlertManager <Integrating with Prometheus>`
* :ref:`See the features you'll gain by integrating AlertManager <Enhanced Prometheus Alerts>`
* :ref:`Configure AI analysis with your Prometheus data <AI Analysis>`
