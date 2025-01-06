Route By Namespace
=============================

You can route alerts based on the Kubernetes namespace they relate to. This is ideal for organizations where different teams "own" specific namespaces.

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

You can apply this method with as many sinks as you like. If the number of sinks is large, consider setting the channel dynamically. See instructions for :ref:`Slack <Dynamic Alert Routing>` or :ref:`MS Teams <Dynamically Route MS Teams Alerts>`.

Troubleshooting Issues
------------------------

For this guide to work, alerts must be tagged with ``namespace`` metadata. It is recommended that you setup a :ref:`Fallback Sink <Stop Further Notifications>` to catch alerts that don't have a namespace.