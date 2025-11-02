Route By Namespace
=============================

You can route alerts based on the Kubernetes namespace they relate to. This is ideal for organizations where different teams "own" specific namespaces.

Prerequisites
----------------

* At least one existing :ref:`sink <sinks-reference>`, such as Slack, Microsoft Teams, Discord, etc.

Setting Up Routing
----------------------

Assume you have an existing sink:

.. code-block:: yaml

    sinksConfig:
    - slack_sink:
        name: slack_app_sink
        slack_channel: app-notifications
        api_key: secret-key

By default, the sink will receive notifications for all namespaces.

Let's create a 2nd copy of the sink and change the Slack channel:

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

Now we have two sinks, both receiving all notifications.

The final step is to restrict notifications for each sink by adding :ref:`scopes <sink-scope-matching>`:

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

Routing for many namespaces
-----------------------------------
Using the above method, you can create one sink for each namespace.

If you have a large number of namespaces, there is an alternative method you can consider: you can define a single sink and set the channel dynamically according to alert metadata. See instructions for :ref:`Slack <Dynamic Alert Routing>` or :ref:`MS Teams <Dynamically Route MS Teams Alerts>`.

Fallback for alerts without a namespace
--------------------------------------------------

The above example assumes that all alerts have ``namespace`` metadata. It is recommended that you setup a :ref:`Fallback Sink <Stop Further Notifications>` to catch alerts that don't have a namespace.