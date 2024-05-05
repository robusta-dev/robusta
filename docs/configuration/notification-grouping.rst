:hide-toc:

Notification Grouping (Currently supported only on Slack)
=========================================================

You can now get a single summary message for a group of alerts,
with the details on every alert in the Slack thread.

.. image:: /images/notification-grouping.png
   :width: 600px
   :align: center



For example, grouping all cluster notifications, into one daily message

.. code-block:: yaml

    sinksConfig:
    - slack_sink:
        # slack integration params, like slack_channel, api_key etc
        grouping:
                              # omitting the ``group_by`` field, will use the default grouping, which is by ``cluster``
          interval: 86400     # group time window, seconds. 1 day
          notification_mode:
            summary:
              threaded: true  # optional, add each alert notification the message thread
              by:
                - identifier  # summary by identifier, which is the alert type

Grouping and summarizing messages
-------------------------------------------------------------------

Some large systems that are being monitored by Robusta could generate
considerable amounts of notifications that are quite similar to each other
(for example, concern one type of a problem occurring over some part of
the cluster). For such cases, Robusta provides a mechanism that will reduce
the amount of clutter in Slack channels by grouping notifications based
on their properties and possibly summarizing the numbers of their
occurrences.

Grouping configuration
-------------------------------------------------------------------

Grouping is enabled by the ``grouping`` section in the Slack sink
config. The parameters you can group on are:

.. code-block:: yaml

    sinksConfig:
    - slack_sink:
        ....
        grouping:
          group_by:
            - cluster         # Group all cluster notifications. This is the default
            - namespace       # Group notifications on the same namespace
            - identifier      # Group notifications with the same type, i.e. KubePodNotReady
            - workload        # Group notifications on the same workload (i.e. ``Deployment``)
            - severity        # Group notifications with the same severity
            - labels:         # Group notifications with the same value on the ``app`` label
              - app
            - annotations:    # Group notifications with the same value on the ``team`` annotation
              - team

          interval: 3600     # group time window, seconds. 1 hour
          notification_mode:
            ...

Configuring multiple ``group_by`` fields, will create a group for each permutation on **all** the group fields.

Omitting the ``group_by`` field will use the default which is ``cluster``.


The ``interval`` setting defines the length of the window over which notifications will be aggregated.
The window starts when the first message belonging to the group arrives,
and ends when the specified interval elapses. If you don't specify the
``interval``, the default value will be 15 minutes.



Sending grouped notifications
-------------------------------------------------------------------

Robusta supports 2 ``notification modes`` for group notifications

- ``summary`` mode - Send a summary of the group notifications, optionally add all notifications on the summary message thread
- ``regular`` mode - Allows sending group messages, only above a configured threshold


``Summary`` notification mode
-------------------------------------------------------------------

The ``summary`` mode allows summarizing the number of notifications in a
succinct way. The summary will be sent to Slack as a single message and will
include information about the number of all the messages in the group.
The summarization will be formatted as a table and done according
to the attributes listed under ``summary.by``. In case ``summary.threaded``
is ``true``, all the Slack notifications belonging to this group will be
appended in a thread under this header message. If ``summary.threaded`` is
``false``, the notifications will not be sent to Slack at all, and only the
summary message will appear.
``summary.by`` attributes are the same as the ``group_by`` attributes listed above.

The information in the summary message will be dynamically updated with
numbers of notifications in the group as they are incoming, regardless
of whether ``summary.threaded`` is enabled or not.

.. code-block::

    sinksConfig:
    - slack_sink:
        ....
        grouping:
          group_by:
            - namespace                # create a summary message for each namespace
          interval: 1800               # 30 min
          notification_mode:
            summary:
              threaded: true           # send all alerts to summary message thread
              by:                      # Summarise by ``identifier`` and ``severity``
                - identifier
                - severity


``Regular`` notification mode
-------------------------------------------------------------------

``regular`` mode allows ignoring first X messages in the group, within the given ``interval``
You have to specify the ``ignore_first`` value. This value will determine the
minimum amount of notifications in any group that would have to occur
in the time specified by ``interval`` before they are sent as Slack
messages. This mode works like a false positive filter - it only triggers
the Slack sink if notifications are incoming at a speed above the set
threshold.

For example, notify on ``ImagePullBackoff`` only if it fires more than 3 times in 5 minutes

.. code-block::

    sinksConfig:
    - slack_sink:
        ...
        scope:                         # filter only on this specific alert
          include:
            - identifier: ImagePullBackoff
        grouping:
          group_by:
            - cluster                  # Group on the whole cluster
          interval: 300                # 5 min
          notification_mode:
            regular:
              ignore_first: 3          # Start sending only after the first 3 notifications in the interval

.. note::

    In the current, initial implementation of this mechanism, the
    statistics of notifications are held in memory and not persisted
    anywhere, so when the Robusta runner dies/restarts, they are lost
    and the counting starts anew.
