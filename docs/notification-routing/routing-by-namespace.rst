Route Alerts By Namespace
=============================

Route alerts based on Kubernetes namespace. Ideal for teams that "own" specific namespaces.

This guide can be applied to all events passing through Robusta, including forwarded Prometheus alerts.

Prerequisites
----------------

* At least one existing :ref:`sink <Sinks Reference>`, such as Slack, Microsoft Teams, Discord, etc.

Setting Up Routing
----------------------

Assume you have an existing sink, in this case Slack:

.. code-block:: yaml

    sinksConfig:
    - slack_sink:
        name: slack_app_sink
        slack_channel: app-notifications
        api_key: secret-key

By default, the sink will receive notifications for all namespaces. Let's duplicate the sink and change only the Slack channel:

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

We now have two sinks, both receiving all notifications. Restrict the notifications for each sink by adding :ref:`matchers <sink-matchers>`:

.. code-block:: yaml

    sinksConfig:
    - slack_sink:
        name: slack_app_sink
        slack_channel: app-notifications
        api_key: secret-key
        scope:
          include:
            - namespace: [app]

    - slack_sink:
        name: slack_system_sink
        slack_channel: system-notifications
        api_key: secret-key
        scope:
          include:
            - namespace: [kube-system]

Apply this final configuration using a :ref:`Helm Upgrade <Simple Upgrade>`.

Alerts will be now routed according to Kubernetes namespace. You can apply this method to as many sinks as you like.

Troubleshooting Issues
------------------------

For this guide to work, alerts must be tagged with ``namespace`` metadata. Alerts without ``namespace`` metadata will be
sent to default sinks (without namespace matchers) if they exist.

If you forward custom Prometheus alerts to Robusta (and don't use Robusta's builtin Prometheus alerts), make sure they
have a ``namespace`` label. Otherwise this method will not work.

.. include:: _routing-further-reading.rst
