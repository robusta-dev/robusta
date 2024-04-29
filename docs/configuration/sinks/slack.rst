Slack
#################

Robusta can report issues and events in your Kubernetes cluster to Slack.

Connecting Slack
------------------------------------------------

When installing Robusta, run ``robusta gen-config`` and follow the prompts. This will use our `official
Slack app <https://slack.com/apps/A0214S5PHB4-robusta?tab=more_info>`_.

**Note: Robusta can only write messages and doesn't require read permissions.**

Alternatively, generate a key by running ``robusta integrations slack`` and set the following Helm values in your
``generated_values.yaml``:

.. code-block:: yaml

     sinks_config:
     # slack integration params
     - slack_sink:
         name: main_slack_sink
         api_key: MY SLACK KEY
         slack_channel: MY SLACK CHANNEL
         max_log_file_limit_kb: <Optional> # (Default: 1000) The maximum allowed file size for "snippets" (in kilobytes) uploaded to the Slack channel. Larger files can be sent to Slack, but they may not be viewable directly within the Slack.
         channel_override: DYNAMIC SLACK CHANNEL OVERRIDE (Optional)

Then do a :ref:`Helm Upgrade <Simple Upgrade>`.

.. note::

    You can change the slack_channel at any time in ``generated_values.yaml``. No need to re-run ``robusta integrations slack``.

Dynamic Slack Channels
-------------------------------------------------------------------

You can set the ``Slack`` channel dynamically, based on the ``cluster name`` or a value of a specific ``label`` or ``annotation``.

This can be done using the optional ``channel_override`` sink parameter.

Allowed values for this parameter are:

- ``cluster_name`` - The Slack channel will be the Robusta ``cluster_name``
- ``labels.foo`` - The Slack channel will be taken from a ``label`` value with the key ``foo``. If no such label, the default channel will be used.
- ``annotations.anno`` - The Slack channel will be taken from an ``annotation`` value with the key ``anno``. If no such annotation, the default channel will be used.

For example:

.. code-block:: yaml

     sinks_config:
     # slack integration params
     - slack_sink:
         name: main_slack_sink
         api_key: xoxb-112...
         slack_channel: my-fallback-channel
         channel_override: "labels.slack"

A replacement pattern is also allowed, using ``$`` sign, before the variable.
For cases where labels or annotations include special characters, such as ``${annotations.kubernetes.io/service-name}``, you can use the `${}` replacement pattern to represent the entire key, including special characters. 
For example, if you want to dynamically set the Slack channel based on the annotation ``kubernetes.io/service-name``, you can use the following syntax:

- ``channel_override: "${annotations.kubernetes.io/service-name}"``


Example:

.. code-block:: yaml

     sinks_config:
     # slack integration params, like slack_channel, api_key etc
     - slack_sink:
         name: main_slack_sink
         api_key: xoxb-112...
         slack_channel: my-fallback-channel
         channel_override: "$cluster_name-alerts-$labels.env-${annotations.kubernetes.io/service-name}"



Using Private Channels
-------------------------------------------------------------------

1. Add Robusta to your workspace using the instructions above.
2. Add the Robusta app to the private channel. See the video below for instructions:

.. raw:: html

    <div style="position: relative; padding-bottom: 62.5%; height: 0;"><iframe src="https://www.loom.com/embed/a0b1a27a54df44fa95c483917b961b11" frameborder="0" webkitallowfullscreen mozallowfullscreen allowfullscreen style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"></iframe></div>

Automatically @mentioning Users
---------------------------------

It is possible to automatically tag users in Slack.

To do so in :ref:`custom playbooks <customPlaybooks>` mention the ``@username`` anywhere in the description:

.. code-block::

    customPlaybooks:
    - triggers:
      - on_kubernetes_warning_event:
          include: ["TooManyPods"]
      actions:
      - create_finding:
          aggregation_key: "too-many-pods-warning"
          severity: HIGH
          title: "Too many pods on $node!"
          description: "@some-user, please take a look." # (1)


.. code-annotations::
    1. @some-user will become a mention in Slack

If you'd like to automatically tag users on builtin alerts, please
`let us know <https://github.com/robusta-dev/robusta/issues/new?assignees=&labels=&template=feature_request.md&title=Tag%20Slack%20Users>`_.
We want to hear requirements.


Grouping and summarizing messages
-------------------------------------------------------------------

Some large systems that are being monitored by Robusta could generate
considerable amounts of notifications that are quite similar to each other
(for example, concern one type of a problem occurring over some part of
the cluster). For such cases, there is a mechanism that will reduce
the amount of clutter in Slack channels by grouping notifications based
on their properties and possibly summarizing the numbers of their
occurrences.

The mechanism is enabled by the ``grouping`` section in the Slack sink
config. The parameters you can group on are basically any values in
the k8s event payload, with one special addition - ``workload`` that
will hold the name of the top-level entity name for the event. Labels
and annotations are supported as described in the example below.

The grouping mechanism supports the ``interval`` setting, which defines
the length of the window over which notifications will be aggregated.
The window starts when the first message belonging to the group arrives,
and ends when the specified interval elapses.

There are two general modes for this functionality, selected by the
subsection ``notification_mode``. For the ``regular`` mode, all the
notification messages that belong to the group will be put in a single
Slack thread, with the first of them being the head (topmost) of the
thread. An additional parameter you can specify in this mode is
``ignore_first``, which can be used to drop some number of initial
messages in the group (useful for cases of very large amount of
notification traffic).

For the ``summary`` mode, the main difference is that the head (topmost)
message in the thread will include a summary of all the messages in the
group. The summarization will be formatted as a table and done according
to the attributes listed under ``summary.by``. In case ``summary.threaded``
is ``true``, all the Slack notifications belonging to this group will be
put as a thread under this header message (``ignore_first`` does not
apply here). If ``summary.threaded`` is ``false``, the notifications
will not be sent to Slack, and only the summary message will appear.

The information in the summary message will be dynamically updated with
numbers of notifications in the group as they are incoming, regardless
of whether ``summary.threaded`` is enabled or not.

.. code-block::

    sinksConfig:
    - slack_sink:
        # slack integration params, like slack_channel, api_key etc
        grouping:
          group_by:
            - workload
            - labels:
              - app
            - annotations:
              - experimental_deployment
          interval: 1800    # group time window, seconds
          notification_mode:
            summary:
              threaded: true
              by:
                - identifier
                - severity

.. note::

    In the current, initial implementation of this mechanism, the
    statistics of notifications are held in memory and not persisted
    anywhere, so when the Robusta runner dies/restarts, they are lost
    and the counting starts anew.


Creating Custom Slack Apps
-------------------------------------------------------------------

If you can't use the `official Slack app <https://slack.com/apps/A0214S5PHB4-robusta?tab=more_info>`_, you can create
your own. This is not recommended for most companies due to the added complexity.

1. `Create a new Slack app. <https://api.slack.com/apps?new_app=1>`_
2. Enable Socket mode in your Slack App.
3. Under "OAuth and Permissions" add the following scopes: chat:write, chat:write.public, files:write, incoming-webhook, and channels:history.
4. Under "Event Subscriptions" add bot user events for message.channels and press "Save Changes".
5. Click "Install into Workspace".
6. Copy the ``Bot User OAuth Token`` from "OAuth and Permissions".
7. Add the token to SinksConfig in your `generated_values.yaml` file.

.. code-block:: yaml
    :name: cb-custom-slack-app-config

    sinksConfig:
    - slack_sink:
        name: main_slack_sink
        slack_channel: <your-channel>
        api_key: <your Bot User OAuth Token>

.. warning::

    When using a custom Slack app, callback buttons are not supported due to complexities in how Slack handles incoming
    messages. :ref:`Contact us if you need assistance. <Getting Support>`
