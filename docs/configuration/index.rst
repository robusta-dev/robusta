:hide-toc:

Configuration Overview
==========================

Follow this guide to configure Robusta after :ref:`installing it <Quick Install>`. Configuration is done using Robusta's Helm values.

Common Settings
^^^^^^^^^^^^^^^^^^

.. grid:: 1 1 2 3
    :gutter: 3

    .. grid-item-card:: :octicon:`book;1em;` Sinks
        :class-card: sd-bg-light sd-bg-text-light
        :link: sinks/index
        :link-type: doc

        Add new destinations for Robusta notifications.

    .. grid-item-card:: :octicon:`book;1em;` Integrate Prometheus
        :class-card: sd-bg-light sd-bg-text-light
        :link: additional-playbooks
        :link-type: doc

        Connect Prometheus, AlertManager, Grafana, and others.

    .. grid-item-card:: :octicon:`book;1em;` Define Alerts
        :class-card: sd-bg-light sd-bg-text-light
        :link: alert-manager
        :link-type: doc

        Create alerts for custom Kubernetes events

Full List of Settings
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can see all of Robusta's settings in the Helm chart:

.. code-block:: yaml

    helm repo add robusta https://robusta-charts.storage.googleapis.com && helm repo update
    helm show values robusta/robusta

.. admonition:: Avoid using the values.yaml file on GitHub
    :class: warning

    It might be tempting to use ``helm/robusta/values.yaml`` in our GitHub repository, but this file wont work.
    It contains empty placeholders filled in during releases.
