Route Alerts By Namespace
=============================

By default, all Robusta notifications are sent to all :ref:`sinks <Sinks Reference>`.

In larger organization, it's common to setup a dedicated notification channel for each team and route alerts accordingly.

In this guide, we'll show how to route notifications based on Kubernetes namespaces, using :ref:`sink matchers <sink-matchers>`.

Prerequisites
----------------

* All least one existing :ref:`sink <Sinks Reference>` must be configured.
* If you send Prometheus alerts via Robusta, they must have appropriate ``namespace`` metadata for Robusta to route them properly. (This is pre-configured for Robusta's bundled Prometheus alerts.)

Setting Up Routing
----------------------

Let's assume you have an existing Slack sink:

.. code-block:: yaml

    sinksConfig:
    - slack_sink:
        name: slack_app_sink
        slack_channel: app-notifications
        api_key: secret-key

First, duplicate duplicate your sink. You need a unique sink for each channel you want to notify in:

.. code-block:: yaml

    sinksConfig:
    - slack_sink:
        name: slack_app_sink
        slack_channel: app-notifications
        api_key: secret-key
    - slack_sink:
        name: slack_system_sink
        slack_channel: system-notifications
        api_key: secret-key

Add a :ref:`matcher <sink-matchers>` to each sink, so it receives a subset of notifications:


.. code-block:: yaml

    sinksConfig:
    - slack_sink:
        name: slack_app_sink
        slack_channel: app-notifications
        api_key: secret-key
        match:
          namespace:
          - app
    - slack_sink:
        name: slack_system_sink
        slack_channel: system-notifications
        api_key: secret-key
        match:
          namespace:
          - kube-system

As always, apply this final configuration using a :ref:`Helm Upgrade <Simple Upgrade>`.

Now alerts will be routed according to Kubernetes namespace.

.. include:: _routing-further-reading.rst