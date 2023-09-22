In-cluster Prometheus
****************************************

Are you already running Prometheus in the same cluster as Robusta? Follow this guide to connect your Prometheus to Robusta. If your Prometheus is in a different cluster refer to the :ref:`Centralized Prometheus` documentation to integrate it with Robusta.

You will need to configure two integrations: a push integration and a pull integration. (Both are necessary.)

Configure Push Integration
============================

A push integration sends alerts to Robusta. Add the config below to the appropriate AlertManager file.

.. note::

    If you're using **kube-prometheus-stack**, add the below config to `AlertManager's config Secret <https://github.com/prometheus-operator/prometheus-operator/blob/main/Documentation/user-guides/alerting.md#managing-alertmanager-configuration>`_. Using other configuration files like Helm values file `will only forward alerts from one namespace <https://github.com/prometheus-operator/prometheus-operator/issues/3750>`_.

.. include:: ./_alertmanager-config.rst

.. include:: ./_testing_integration.rst

.. include:: ./_pull_integration.rst
