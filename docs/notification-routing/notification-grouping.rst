.. _notification-grouping:

Notification Grouping (Slack Only)
=========================================================

You can consolidate alerts into Slack threads to reduce the number of notifications.
Each thread begins with a summary message that updates in real time as new alerts are received.

.. image:: /images/notification-grouping.png
   :width: 600px
   :align: center

*Example: Alerts from a cluster are consolidated into a daily summary message, with individual alerts in the thread.*

Configuring Notification Grouping
----------------------------------

To enable grouping of notifications, add a ``grouping`` block to your Slack sink:

.. code-block:: yaml

    sinksConfig:
    - slack_sink:
        # Standard Slack configuration settings such as 'slack_channel' and 'api_key'
        ...
        grouping:
          group_by: ["cluster"]     # Default setting: groups all notifications into one daily summary
          interval: 86400           # Time window for grouping in seconds (86400s = 1 day)
          notification_mode:
            summary:
              threaded: true        # Optional: includes each new alert in the message thread
              by:
                - identifier        # Show a table in the summary message listing identifiers - i.e. AlertNames

Customizing the way alerts are grouped
-------------------------------------------

Instead of creating a single thread with all alerts in a given day, you can group alerts into different threads by specifying a grouping criteria:

.. code-block:: yaml

    sinksConfig:
      - slack_sink:
          ...
          grouping:
            group_by:
              - cluster       # Default: groups all cluster-related notifications
              - namespace     # Groups notifications within the same namespace
              - identifier    # Groups notifications by alert name, e.g., 'KubePodNotReady'
              - workload      # Groups notifications by workload, e.g., 'Deployment'
              - severity      # Groups notifications by severity level
              - labels:       # Groups notifications by specific label values
                  - app
              - annotations:  # Groups notifications by specific annotation values
                  - team
            interval: 3600    # Grouping interval in seconds (3600s = 1 hour)

Each unique combination of ``group_by`` fields will create it's own group.
Leaving ``group_by`` unset will default to creating a single group with all alerts from the cluster, as shown above.

You can control how often summary messages are sent with the ``interval`` setting. When the first alert in a group arrives, a new group (and Slack thread) is created. That group is used until time ``interval`` passes.

Customizing the notifications
-------------------------------

Robusta supports two settings for ``notification_mode`` that behave differently: **Summary Mode** and **Regular Mode**. Up until now, everything described uses **Summary Mode**.

Summary Mode
**************
Summary Mode is the main grouping mode. It sends threaded summaries, as described above.

The main options for ``summary`` mode are ``threaded`` and ``by``:

.. code-block:: yaml

    sinksConfig:
      - slack_sink:
          ...
          grouping:
            group_by:
              - namespace
            interval: 1800
            notification_mode:
              summary:
                threaded: true
                by:
                  - identifier
                  - severity

The ``threaded`` setting controls whether individual alerts are sent to the Slack thread, or only a summary message is created. When false, the summary message will show up but individual alerts wont be sent at all. When true, both the summary is created, and individual alerts sent to a thread underneath the summary.

The ``by`` setting controls the table shown in the summary message. It accepts the same fields as ``group_by`` and can be used to build a custom breakdown report.

Regular Mode
**************
Regular Mode disables threaded summaries and sends notifications "the usual way", ungrouped. This is useful when combined with  ``grouping`` to notify when at least X alerts have been received in a group.

For example, to filter out false positives and notify on ``ImagePullBackoff`` only if it fires more than 3 times in 5 minutes, you can send notifications in ``regular`` mode  with ``group_by`` and ``ignore_first`` criteria:

.. code-block::

    sinksConfig:
    - slack_sink:
        ...
        scope:                         # filter only on this specific alert
          include:
            - identifier: ImagePullBackoff
        grouping:
          group_by:
            - cluster                  # all alerts will be counted together for the purpose of ignore_first
          interval: 300                # 5 min
          notification_mode:
            regular:
              ignore_first: 3          # Start sending only after the first 3 notifications in the interval

Limitations
---------------
Notification statistics are currently held in memory and will reset if the Robusta runner restarts.
