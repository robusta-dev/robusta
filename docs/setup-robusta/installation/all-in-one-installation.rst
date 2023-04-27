:tocdepth: 2
:globaltoc_collapse: false

Monitor Kubernetes from Scratch
####################################
*Estimated time: 5 minutes*

Setup Kubernetes monitoring from scratch, using the all-in-one Robusta and Prometheus
package. This is the recommended way to monitor your cluster.

Prerequisites
---------------------

* A :ref:`supported Kubernetes cluster <Supported Clusters>`
* Helm

.. include:: ../_questions.rst

.. jinja::
   :inline-ctx: { "gen_config_flags": "--enable-prometheus-stack" }
   :header_update_levels:
   :file: setup-robusta/installation/_generate_config.jinja

.. include:: ./_helm_install.rst

.. include:: ./_see_robusta_in_action.rst

Next Steps
---------------------------------

:ref:`See how Robusta improves Prometheus <builtin-alert-enrichment>`.
