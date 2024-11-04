Route By Namespace
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

We now have two sinks, both receiving all notifications. Restrict the notifications for each sink by adding :ref:`scopes <sink-matchers>`:

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

Alerts will be now routed according to Kubernetes namespace.

You can apply this method with as many sinks as you like. If the number of sinks is large, consider setting the channel dynamically. (See instructions for :ref:`Slack <Dynamic Alert Routing>` or :ref:`MS Teams <Dynamically Route MS Teams Alerts>`.)

Troubleshooting Issues
------------------------

For this guide to work, alerts must be tagged with ``namespace`` metadata. Alerts without ``namespace`` metadata will be
sent to default sinks (without namespace matchers) if they exist.

If you forward custom Prometheus alerts to Robusta (and don't use Robusta's builtin Prometheus alerts), make sure they
have a ``namespace`` label. Otherwise this method will not work.
