kube-prometheus-stack
*********************************************

Connect an existing kube-prometheus-stack to Robusta, by configuring two integrations: a push integration and a pull integration.

Configure Push Integration
============================

Configure AlertManger to push alerts to Robusta, by editing the `AlertManager config Secret <https://github.com/prometheus-operator/prometheus-operator/blob/main/Documentation/user-guides/alerting.md#managing-alertmanager-configuration>`_, and adding a receiver and route:

.. include:: ./_alertmanager-config.rst

.. include:: ./_testing_integration.rst

.. details:: Why use a secret instead of editing AlertManagerConfig?

    In theory, you can configure an AlertmanagerConfig instead of using a secret. However, this is **not** recommended as it `will only forward alerts from one namespace <https://github.com/prometheus-operator/prometheus-operator/issues/3750>`_.

.. include:: ./_pull_integration.rst

.. include:: ./_additional_settings.rst
