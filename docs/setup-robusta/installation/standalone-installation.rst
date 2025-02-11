:tocdepth: 2
:globaltoc_collapse: false

.. _install-barebones:

Barebones Installation
####################################

*Estimated time: 5 minutes*

Robusta normally uses the APIServer and Prometheus as data-sources. It's possible to disable Prometheus and still benefit
from Robusta's other features, like notifications on crashing pods and OOMKills.

.. warning::

   Most people should install with Prometheus **instead** of this tutorial.

   Robusta is useful standalone, but Prometheus makes it even better!

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