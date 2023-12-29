In-cluster Prometheus
****************************************

Are you already running Prometheus in the same cluster as Robusta? Follow this guide to connect your Prometheus to Robusta. If your Prometheus is in a different cluster refer to the :ref:`Centralized Prometheus` documentation to integrate it with Robusta.

You will need to configure two integrations: one to send alerts to Robusta and another to let Robusta query metrics and create silences.

Send alerts to Robusta
============================

Add the config below to the appropriate AlertManager file:

.. include:: ./_alertmanager-config.rst

.. include:: ./_testing_integration.rst

.. include:: ./_pull_integration.rst
