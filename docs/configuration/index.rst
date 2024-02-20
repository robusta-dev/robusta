:hide-toc:

Integrations Overview
==========================

Follow this guide to integrate Robusta after :ref:`installing it <install>`. Integrations are done using Robusta's Helm values.

Common Settings
^^^^^^^^^^^^^^^^^^

.. grid::
    :gutter: 3

    .. grid-item-card:: :octicon:`book;1em;` Configure Sinks
        :class-card: sd-bg-light sd-bg-text-light
        :link: configuring-sinks
        :link-type: doc

        Send notifications from Robusta to external systems.

    .. grid-item-card:: :octicon:`book;1em;` Integrate Prometheus
        :class-card: sd-bg-light sd-bg-text-light
        :link: alertmanager-integration/index
        :link-type: doc

        Connect Prometheus, AlertManager, Grafana, and others.



All Settings
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

All of Robusta's settings are listed as Helm chart values:

.. code-block:: yaml

    helm repo add robusta https://robusta-charts.storage.googleapis.com && helm repo update
    helm show values robusta/robusta

.. admonition:: Avoid using the values.yaml file on GitHub
    :class: warning

    It might be tempting to use ``helm/robusta/values.yaml`` in our GitHub repository, but this file wont work.
    It contains empty placeholders filled in during releases.
