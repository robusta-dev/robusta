kube-prometheus-stack and Prometheus Operator
*********************************************

If you've installed the kube-prometheus-stack or the Prometheus Operator independently (not via Robusta), inform AlertManager about Robusta using a `Kubernetes Secret <https://github.com/prometheus-operator/prometheus-operator/blob/main/Documentation/user-guides/alerting.md#managing-alertmanager-configuration>`_. The Prometheus Operator will pass this secret to AlertManager, which will then push alerts to Robusta by webhook.
.. Let's add the AlertManager config into a `Kubernetes Secret <https://github.com/prometheus-operator/prometheus-operator/blob/main/Documentation/user-guides/alerting.md#managing-alertmanager-configuration>`_. 
.. The Prometheus Operator will pass this secret to AlertManager, which will then push alerts to Robusta by webhook.
This guide walks you through configuring your Kube Prometheus Stack to push alerts to Robusta and also configuring Robusta to pull additional data when needed.

Configure Push Integration
============================
To configure the secret, copy the below configuration and place it in the appropriate Kubernetes Secret.

.. include:: ./_alertmanager-config.rst

After you configure AlertManager, you can test it works properly, by creating a demo alert:

.. code-block:: bash

    robusta demo-alert

Within a few minutes, you should see the demo alert in the Robusta UI, Slack, and any other sinks you configured.

.. details:: Why do I see a banner in the UI that "Alerts won't show up"?
    :class: warning

    This notification is displayed until AlertManager sends the first alert to Robusta.

.. details:: Why use a secret instead of editing AlertManagerConfig?

    In theory, you can configure an AlertmanagerConfig instead of using a secret. However, this is **not** recommended.
    It `will only forward alerts from one namespace <https://github.com/prometheus-operator/prometheus-operator/issues/3750>`_.

.. include:: ./_pull_integration.rst

.. include:: ./_additional_settings.rst