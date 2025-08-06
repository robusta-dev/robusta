In-cluster Prometheus
****************************************

Here's how to integrate an existing Prometheus with Robusta in the same cluster:

* Send alerts to Robusta by adding a receiver to AlertManager
* Point Robusta at Prometheus so it can query metrics and silence alerts
    * Robusta will attempt auto-detection, so this is not always necessary!

If your Prometheus is in a different cluster, refer to :ref:`External Prometheus`.

Send Alerts to Robusta
============================

.. include:: ./_alertmanager-config.rst

.. include:: ./_testing_integration.rst

.. include:: ./_pull_integration.rst
