:hide-toc:

Overview
==========================

Learn how to configure Robusta once its installed.

Need to install Robusta or configure GitOps? See :ref:`Installation <Quick Install>` first.

Popular Settings
^^^^^^^^^^^^^^^^^^

.. grid:: 1 1 2 3
    :gutter: 3

    .. grid-item-card:: :octicon:`book;1em;` Add Sinks
        :class-card: sd-bg-light sd-bg-text-light
        :link: sinks/index
        :link-type: doc

        Add new destinations for Robusta notifications.

    .. grid-item-card:: :octicon:`book;1em;` Integrate Prometheus
        :class-card: sd-bg-light sd-bg-text-light
        :link: additional-playbooks
        :link-type: doc

        Receive data from Prometheus, AlertManager, Grafana, and more.

    .. grid-item-card:: :octicon:`book;1em;` Define Alerts
        :class-card: sd-bg-light sd-bg-text-light
        :link: alert-manager
        :link-type: doc

        Setup alerts for custom Kubernetes events

All Settings
^^^^^^^^^^^^^^^

Robusta is configured using Helm values.

All possible values for Robusta can be listed like so:

.. code-block:: yaml

    helm repo add robusta https://robusta-charts.storage.googleapis.com && helm repo update
    helm show values robusta/robusta

.. admonition:: Do not use the values.yaml file on GitHub
    :class: warning

    It's tempting to look at ``helm/robusta/values.yaml`` in our GitHub repo for reference.
    This is the wrong file to use, as it has empty placeholders that are filled in for releases.
