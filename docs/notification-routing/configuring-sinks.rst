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

For all options, refer to :ref:`All Sink Options`.

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


All Sink Options
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Here is an example showing common sink options:

.. code-block:: yaml

    sinksConfig:
    - slack_sink:                     # sink type
        name: my_sink_name            # name that uniquely identifies this sink in Robusta
        scope: {}                     # optional - filter notifications sent to this sink
        activity: {}                  # optional - enable/disable sink according to time of day/week
        stop: false                   # optional - stop notifications from continuing to subsequent sinks
        grouping: {}                  # optional - use grouping to reduce the number of notifications (i.e. group into slack threads)
        default: true                 # optional - disable this sink by default

        # sink-specific parameters - e.g. for Slack, some options are shown below
        # api_key: xoxb-112...
        # slack_channel: general-alerts

Description of each option:

+------------------+---------------------------------------------------------+----------------------------------------------------------+-----------------------------------------------+
| Parameter Name   | Description                                             | Default                                                  | Docs                                          |
+==================+=========================================================+==========================================================+===============================================+
| name             | A unique name for this sink in Robusta                  | -                                                        | -                                             |
+------------------+---------------------------------------------------------+----------------------------------------------------------+-----------------------------------------------+
| scope            | Filters the notifications sent to this sink             | *undefined* - all notifications are sent (unless already |                                               |
|                  |                                                         | sent a previou sink that set `stop: true`)               | :ref:`Routing (scopes) <sink-scope-matching>` |
+------------------+---------------------------------------------------------+----------------------------------------------------------+-----------------------------------------------+
| activity         | Controls the hours this sink is active                  | *undefined* - active all hours and all days of the week  | :ref:`Route by Time`                          |
+------------------+---------------------------------------------------------+----------------------------------------------------------+-----------------------------------------------+
| stop             | Should notifications continue to subsequent sinks?      | false - notification sent to this sink will continue to  | :ref:`Stop Further Notifications`             |
|                  |                                                         | subsequent sinks                                         |                                               |
+------------------+---------------------------------------------------------+----------------------------------------------------------+-----------------------------------------------+
| grouping         | Currently only impacts the Slack sink, where it controls| *undefined* (disabled)                                   | :ref:`Grouping <notification-grouping>`       | 
|                  | the creation of threads and the grouping of many        |                                                          |                                               |
|                  | notifications into one message                          |                                                          |                                               |
+------------------+---------------------------------------------------------+----------------------------------------------------------+-----------------------------------------------+
| default          | Is this sink enabled by default? When false, this sink  | true - this sink is enabled by default                   | :ref:`Alternative Routing Methods`            |
|                  | only accepts notifications from customPlaybooks which   |                                                          |                                               |
|                  | explicitly named this sink (if scope is set, it will    |                                                          |                                               |
|                  | still filter those notifications)                       |                                                          |                                               |
+------------------+---------------------------------------------------------+----------------------------------------------------------+-----------------------------------------------+
| *sink specific*  | Parameters specific to the sink type, like api_key for  | -                                                        | :ref:`sink-specific docs <Sinks Reference>`   |
| *parameters*     | Slack and webhook_url for MSTeams                       |                                                          |                                               |
+------------------+---------------------------------------------------------+----------------------------------------------------------+-----------------------------------------------+

Learn More
^^^^^^^^^^^^

* 🔔 :ref:`All Sinks <Sinks Reference>`
* ↳ :ref:`Routing (scopes) <sink-scope-matching>`