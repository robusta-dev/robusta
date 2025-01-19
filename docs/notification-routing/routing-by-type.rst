Route By Alert Name
=============================

By default, Robusta notifications are sent to all :ref:`sinks <Sinks Reference>`.

In this guide, you'll learn to route alerts by their name:

* *KubePodCrashLooping* alerts will be sent to a *#crash-alerts* channel
* All other alerts will be sent to *#general-alerts*

Prerequisites
----------------

All least one existing :ref:`sink <Sinks Reference>` must be configured. Below, we'll assume it's a Slack sink.

Setting Up Routing
----------------------

Assume you have an existing Slack sink as follows:

.. code-block:: yaml

    sinksConfig:
    - slack_sink:
        name: sink1
        slack_channel: general-alerts
        api_key: secret-key

The first step is to duplicate your sink. You need two unique sinks - one for each channel:

.. code-block:: yaml

    sinksConfig:
    - slack_sink:
        name: sink2
        slack_channel: crash-alerts
        api_key: secret-key
    - slack_sink:
        name: sink1
        slack_channel: general-alerts
        api_key: secret-key

The sinks are nearly identical - only the ``name`` and ``slack_channel`` parameters vary:

* The ``name`` field identifies this sink in Robusta and can be chosen arbitrarily - so long as it is unique between sinks
* The ``slack_channel`` field should match a channel in your Slack account

The next step is to update the configuration so that ``#crash-alerts`` receives a subset of alerts:

.. code-block:: yaml

    sinksConfig:
    - slack_sink:
        name: sink2
        slack_channel: crash-alerts
        api_key: secret-key
        - scope:
            include:
            # only send notifications for the KubePodCrashLooping alert
            - identifier: [KubePodCrashLooping]
    - slack_sink:
        name: sink1
        slack_channel: general-alerts
        api_key: secret-key

We added an :ref:`inclusion scope <sink-matchers>` for the ``#crash-alerts`` channel. To filter alerts by their name, use the ``identifier`` field which corresponds to the Prometheus alert name.

One final step: we must update the default sink to exclude *KubePodCrashLooping*. You can do this two ways:

**Option 1:** add an exclusion scope:

.. code-block:: yaml

    sinksConfig:
    - slack_sink:
        name: sink2
        slack_channel: crash-alerts
        api_key: secret-key
        - scope:
            include:
            # only send notifications for the KubePodCrashLooping alert
            - identifier: [KubePodCrashLooping]
    - slack_sink:
        name: sink1
        slack_channel: general-alerts
        api_key: secret-key
        - scope:
            exclude:
            # don't send notifications for the KubePodCrashLooping alert
            - identifier: [KubePodCrashLooping]

**Option 2:** use ``stop: true`` to prevent alerts from propogating after a match:

.. code-block:: yaml

    sinksConfig:
    - slack_sink:
        name: sink2
        slack_channel: crash-alerts
        api_key: secret-key
        # add the following line!
        stop: true
        - scope:
            include:
            - identifier: [KubePodCrashLooping]
    - slack_sink:
        name: sink1
        slack_channel: general-alerts
        api_key: secret-key

Whichever way you chose, now *KubePodCrashLooping* alerts are sent to ``#crash-alerts``. Other alerts go to ``#general-alerts``.
