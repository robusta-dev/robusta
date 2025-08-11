In-cluster AlertManager Integration
****************************************

This guide shows how to send alerts from an existing AlertManager to Robusta in the same cluster.

If your AlertManager is in a different cluster, refer to :ref:`External Prometheus`.

For configuring metric querying and advanced Prometheus settings, see :doc:`/configuration/metric-providers-in-cluster`.

Send Alerts to Robusta
============================

.. include:: ./_alertmanager-config.rst

.. include:: ./_testing_integration.rst

.. include:: ./_pull_integration.rst
