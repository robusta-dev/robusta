Kube-Prometheus-Stack and Prometheus Operator
*********************************************

.. If you've installed the kube-prometheus-stack or the Prometheus Operator independently (not via Robusta), inform AlertManager about Robusta using a `Kubernetes Secret <https://github.com/prometheus-operator/prometheus-operator/blob/main/Documentation/user-guides/alerting.md#managing-alertmanager-configuration>`_.


.. Here's a step-by-step guide on how to integrate your Kube Prometheus Stack with Robusta.

This guide walks you through integrating your Kube-Prometheus-Stack or the Prometheus Operator with Robusta. You will need to configure two integrations: both a push integration and a pull integration.

.. You must inform the AlertManager about Robusta using a `Kubernetes Secret <https://github.com/prometheus-operator/prometheus-operator/blob/main/Documentation/user-guides/alerting.md#managing-alertmanager-configuration>`_. The Prometheus Operator will pass this secret to AlertManager, which will then push alerts to Robusta by webhook.

Configure Push Integration
============================

The AlertManager must be informed about Robusta using a `Kubernetes Secret <https://github.com/prometheus-operator/prometheus-operator/blob/main/Documentation/user-guides/alerting.md#managing-alertmanager-configuration>`_. The Prometheus Operator will pass this secret to AlertManager, which will then push alerts to Robusta by webhook.

To configure it, you must add a receiver and route to AlertManager's configuration.

Copy the configuration below and place it in the appropriate Kubernetes Secret.

.. include:: ./_alertmanager-config.rst

.. include:: ./_testing_integration.rst

.. details:: Why use a secret instead of editing AlertManagerConfig?

    In theory, you can configure an AlertmanagerConfig instead of using a secret. However, this is **not** recommended.
    It `will only forward alerts from one namespace <https://github.com/prometheus-operator/prometheus-operator/issues/3750>`_.

.. include:: ./_pull_integration.rst

.. include:: ./_additional_settings.rst
