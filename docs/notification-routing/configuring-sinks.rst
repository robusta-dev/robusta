.. _sinks-overview:

Defining Sinks
==========================

Robusta can send notifications to various destinations, called sinks.

For a list of all sinks, refer to :ref:`Sinks Reference`.

A Simple Sink Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Sinks are defined in Robusta's Helm chart, using the ``sinksConfig`` value.

For example, lets add a :ref:`Microsoft Teams Sink <MS Teams sink>`:

.. code-block:: yaml

    sinksConfig:
    - ms_teams_sink:                  # sink type
        name: my_teams_sink           # name that uniquely identifies this sink in Robusta
        webhook_url: <placeholder>    # the webhook URL for MSTeams - each sink has different parameters like this

More Sink Options
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Here are some more options you can set on sinks:

.. code-block:: yaml

    sinksConfig:
    - ms_teams_sink:                  # sink type
        name: my_teams_sink           # name that uniquely identifies this sink in Robusta
        stop: false                   # optional - covered in the next tutorial
        scope: {}                     # optional - covered in the next tutorial
        default: true                 # optional - covered in the next tutorial

        # sink-specific parameters
        webhook_url: <placeholder>

The ``stop``, ``scope``, and ``default`` fields are used for :ref:`routing (scopes) <sink-scope-matching>`.

Defining Multiple Sinks
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
You can define multiple sinks. By default, notifications will be sent to all of them.

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

Learn More
^^^^^^^^^^^^

* 🔔 :ref:`All Sinks <Sinks Reference>`
* ↳ :ref:`Routing (scopes) <sink-scope-matching>`