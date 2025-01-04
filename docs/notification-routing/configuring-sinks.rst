.. _sinks-overview:

Notification Basics
==========================

Robusta can send notifications to various destinations, called sinks. For a list of all sinks, refer to :ref:`Sinks Reference`.

Defining Sinks
^^^^^^^^^^^^^^^^^^
Sinks are defined in Robusta's Helm chart, using the ``sinksConfig`` value.

For example, lets add a :ref:`Microsoft Teams <MS Teams sink>`:

.. code-block:: yaml

    sinksConfig:
    - ms_teams_sink:                  # sink type
        name: my_teams_sink           # arbitrary name
        webhook_url: <placeholder>    # a sink-specific parameter
        stop: false                   # optional (see `Routing Alerts to only one Sink`)
        scope: {}                     # optional routing rules
        default: true                 # optional (see below)

In addition to the above attributes, some sinks have additional attributes that can be found in their documentation.

Defining Multiple Sinks
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
You can define multiple sinks and by default, notifications will be sent to all of them.

In the following example, we define a :ref:`Slack sink <Slack>` and a :ref:`MS Teams sink <MS Teams>` without any routing rules, so both sinks receive all notifications:

.. code-block:: yaml

    sinksConfig:
    - slack_sink:
        name: my_slack_sink
        slack_channel: my-channel
        api_key: secret-key
    - ms_teams_sink:
        name: my_teams_sink
        webhook_url: <placeholder>

To selectively send notifications to different sinks, refer to :ref:`routing (scopes) <sink-scope-matching>`.

See Also
^^^^^^^^^^^^

🔔 :ref:`All Sinks <Sinks Reference>`
