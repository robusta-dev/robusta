:tocdepth: 2

.. _install-barebones:

Use HolmesGPT without Prometheus
####################################

*Estimated time: 5 minutes*

Robusta's AI Agent works with many monitoring tools beyond Prometheus - including Datadog, New Relic, PagerDuty, and more. This installation method is ideal when you already have monitoring infrastructure in place and want to enhance it with Robusta's AI-powered investigation and automation capabilities.

.. note::

   This installation method is most relevant for Robusta SaaS users who want to integrate with existing monitoring tools. The AI Agent can analyze alerts from multiple sources and provide intelligent investigation across your entire observability stack.
   
   If you're looking for standalone open source monitoring, you should install Robusta with Prometheus using the :ref:`all-in-one installation <install-with-prometheus>` instead.

Prerequisites
---------------------

* A :ref:`supported Kubernetes cluster <Supported Clusters>`
* Helm

.. jinja::
   :inline-ctx: {"gen_config_flags": "--no-enable-prometheus-stack"}
   :header_update_levels:
   :file: setup-robusta/installation/_generate_config.jinja

.. include:: ./_helm_install_no_prometheus.inc.rst

.. include:: ./_see_robusta_in_action.rst


Next Steps
---------------------------------

* :ref:`Track Failed Kubernetes Jobs`