In-cluster Prometheus
****************************************

Already running Prometheus/Kube-prometheus-stack? Connect it to Robusta.

You will need to configure two integrations: a push integration and a pull integration. (Both are necessary.)

This guide assumes Prometheus is running in the same cluster as Robusta. If not, refer to :ref:`Centralized Prometheus`.

Configure Push Integration
============================

A push integration sends alerts to Robusta. Configure it by updating AlertManager's configuration. For kube-prometheus-stack, edit `AlertManager's config Secret <https://github.com/prometheus-operator/prometheus-operator/blob/main/Documentation/user-guides/alerting.md#managing-alertmanager-configuration>`_:

.. include:: ./_alertmanager-config.rst

.. details:: Why use a secret instead of editing AlertManagerConfig?

    In theory, you can modify the AlertmanagerConfig instead. However, this is **not** recommended as it `will only forward alerts from one namespace <https://github.com/prometheus-operator/prometheus-operator/issues/3750>`_.


.. include:: ./_testing_integration.rst

.. include:: ./_pull_integration.rst
