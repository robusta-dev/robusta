In-cluster Prometheus
****************************************

Already running Prometheus? Connect it to Robusta.

You will need to configure two integrations: a push integration and a pull integration. (Both are necessary.)

This guide assumes Prometheus is running in the same cluster as Robusta. If not, refer to :ref:`Centralized Prometheus`.

Configure Push Integration
============================

A push integration sends alerts to Robusta. Configure it by updating AlertManager's configuration:

.. include:: ./_alertmanager-config.rst

.. include:: ./_testing_integration.rst

.. include:: ./_pull_integration.rst
