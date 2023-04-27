:tocdepth: 2
:globaltoc_collapse: false

Integrate with Existing Prometheus
####################################
*Estimated time: 5 minutes*

Install Robusta alongside an existing Prometheus. See what Robusta can do.

Prerequisites
---------------------

* A :ref:`supported Kubernetes cluster <Supported Kubernetes Clusters>`
* A Prometheus installation
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

Integrate Robusta with AlertManager:

* :ref:`Follow a guide to integrate AlertManager <Integrating AlertManager and Prometheus>`.
* :ref:`See the features you'll gain by integrating AlertManager <Enhanced Prometheus Alerts>`.
