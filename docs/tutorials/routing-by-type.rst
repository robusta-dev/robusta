Route Alerts By Type
=============================

By default, all Robusta notifications are sent to all :ref:`sinks <Sinks Reference>`.

It can be useful to send alerts of a *specific type* to a dedicated channel.

In this guide, we'll show how to route notifications for crashing pods to a specific Slack channel. All other notifications
will be sent to the usual channel.

Prerequisites
----------------

All least one existing :ref:`sink <Sinks Reference>` must be configured.

Setting Up Routing
----------------------

This guide applies to all sink types. For simplicity's sake we'll assume you have an existing Slack sink:

.. code-block:: yaml

    sinksConfig:
    - slack_sink:
        name: slack_app_sink
        slack_channel: main-notifications
        api_key: secret-key

The first step is to duplicate your sink. You need two unique sinks - one for each channel:

.. code-block:: yaml

    sinksConfig:
    - slack_sink:
        name: main_sink
        slack_channel: main-notifications
        api_key: secret-key
    - slack_sink:
        name: crashloopbackoff_slack_sink
        slack_channel: crashpod-notifications
        api_key: secret-key

The sinks are nearly identical - only the ``name`` and ``slack_channel`` parameters vary.

Now lets add a :ref:`matcher <sink-matchers>` to each sink, so it receives a subset of notifications:

.. code-block:: yaml

    sinksConfig:
    - slack_sink:
        name: main_sink
        slack_channel: main-notifications
        api_key: secret-key
        - scope:
            exclude:
          # don't match notifications related to crashing pods
              - identifier: report_crash_loop

   - slack_sink:
        name: crashloopbackoff_slack_sink
        slack_channel: crash-notifications
        api_key: secret-key
        - scope:
            include:
        # match notifications related to crashing pods
              - identifier: report_crash_loop


Now the ``crash-notifications`` channel will receive crashpod notifications and all other notifications will go to the
``main-notifications`` channel.

.. include:: _routing-further-reading.rst
