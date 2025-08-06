Slack
#################

Robusta can proxy Prometheus alerts to Slack, adding powerful features like :ref:`AI investigation <AI Analysis>`, :ref:`smart grouping <notification-grouping>` and more.

.. image:: /images/robusta-slack.png
   :width: 600px
   :align: center

Robusta can send both Prometheus alerts and direct Kubernetes notifications (pod crashes, deployment changes, etc.) to Slack.

.. warning::

   If you are using the Slack sink and a Robusta version prior to 0.10.29, we **highly recommend** `upgrading <https://docs.robusta.dev/master/setup-robusta/upgrade.html>`_, as Slack has deprecated their older APIs. This older API will be sundown March 11, 2025. This will cause the slack sink to stop working for older versions of Robusta. 

   Follow `these steps <https://docs.robusta.dev/master/setup-robusta/upgrade.html#helm-upgrade>`_ to upgrade.

Quick Start
------------------------------------------------

**Option 1: Automatic Setup (Recommended)**

When installing Robusta, run ``robusta gen-config`` and follow the prompts. This automatically configures Slack using our `official
Slack app <https://slack.com/apps/A0214S5PHB4-robusta?tab=more_info>`_.

Note: Robusta can only write messages and doesn't require read permissions.

**Option 2: Manual Configuration**

Generate a Slack API key by running ``robusta integrations slack``, then add to your ``generated_values.yaml``:

.. code-block:: yaml

     sinksConfig:
     # slack integration params
     - slack_sink:
         name: main_slack_sink
         api_key: MY SLACK KEY  # to avoid putting your key in Helm values, see below
         slack_channel: MY SLACK CHANNEL
         max_log_file_limit_kb: <Optional> # (Default: 1000) The maximum allowed file size for "snippets" (in kilobytes) uploaded to the Slack channel. Larger files can be sent to Slack, but they may not be viewable directly within the Slack.
         channel_override: DYNAMIC SLACK CHANNEL OVERRIDE (Optional)
         investigate_link: true/false # optional, if false no investigate links/buttons will be included in Slack messages

.. warning::

    If you don't want to put your Slack key in Helm values, you can use a secret. See the :ref:`Managing Secrets <Managing Secrets>` section for more information.

Then do a :ref:`Helm Upgrade <Simple Upgrade>` to apply the new configuration.

Notification Grouping
-----------------------------
Slack allows grouping multiple notifications into summary messages and Slack threads. Refer to :ref:`Grouping <notification-grouping>` for details.

.. image:: /images/notification-grouping.png
   :width: 600px
   :align: center

Dynamic Alert Routing
-------------------------------------------------------------------

You can route alerts to different Slack channels by defining several Slack sinks. See :ref:`Route By Namespace` for an example.

Alternatively, if the number of channels is large, you can define a single Slack sink and use the ``channel_override`` parameter to read the destination channel from alert metadata.

Allowed values for ``channel_override`` are:

- ``cluster_name`` - The Slack channel will be the Robusta ``cluster_name``
- ``labels.foo`` - The Slack channel will be taken from a ``label`` value with the key ``foo``. If no such label, the default channel will be used.
- ``annotations.anno`` - The Slack channel will be taken from an ``annotation`` value with the key ``anno``. If no such annotation, the default channel will be used.

For example:

.. code-block:: yaml

     sinksConfig:
     # slack integration params
     - slack_sink:
         name: main_slack_sink
         api_key: xoxb-112...
         slack_channel: my-fallback-channel
         channel_override: "labels.slack"   # read the 'slack' label from the alert and route to that channel

A replacement pattern is also allowed, using ``$`` sign, before the variable.
For cases where labels or annotations include special characters, such as ``${annotations.kubernetes.io/service-name}``, you can use the `${}` replacement pattern to represent the entire key, including special characters.
For example, if you want to dynamically set the Slack channel based on the annotation ``kubernetes.io/service-name``, you can use the following syntax:

- ``channel_override: "${annotations.kubernetes.io/service-name}"``


Example:

.. code-block:: yaml

     sinksConfig:
     # slack integration params, like slack_channel, api_key etc
     - slack_sink:
         name: main_slack_sink
         api_key: xoxb-112...
         slack_channel: my-fallback-channel
         channel_override: "$cluster_name-alerts-$labels.env-${annotations.kubernetes.io/service-name}"

Redirect to Platform
-------------------------------------------------------------------

By default, Slack notifications include buttons to view more information in the Robusta SaaS platform.
If you don't use Robusta SaaS you can modify these links to point at Prometheus instead.
To do so, set prefer_redirect_to_platform: false.

For example:

.. code-block:: yaml

     sinksConfig:
     # slack integration params
     - slack_sink:
         name: main_slack_sink
         api_key: xoxb-112...
         slack_channel: my-fallback-channel
         prefer_redirect_to_platform: false


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


Creating Custom Slack Apps
-------------------------------------------------------------------

If you can't use the `official Slack app <https://slack.com/apps/A0214S5PHB4-robusta?tab=more_info>`_, you can create
your own. This is not recommended for most companies due to the added complexity.

1. `Create a new Slack app <https://api.slack.com/apps?new_app=1>`_
2. Enable Socket mode in your Slack App.
3. Under "OAuth and Permissions" add the following scopes: chat:write, chat:write.public, files:write, incoming-webhook, and channels:history.
4. Under "Event Subscriptions" add bot user events for message.channels and press "Save Changes".
5. Click "Install into Workspace".
6. Copy the ``Bot User OAuth Token`` from "OAuth and Permissions".
7. Add the token to sinksConfig in your `generated_values.yaml` file.

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


Message Templating
-------------------------------------------------------------------

Slack messages can be customized using Jinja2 templates. Robusta includes default templates that match the standard format, but you can override them for custom formatting.

To use custom templates change your `slack_sink` to `slack_sink_preview`, and add your templates to the ``slack_custom_templates`` parameter:

.. code-block:: yaml

   sinksConfig:
   - slack_sink_preview:
       api_key: xoxb-198...
       name: preview_slack_sink
       slack_channel: demo-slack-preview
       slack_custom_templates:
         custom_template.j2: |-
           {
              "type": "header",
              "text": {
                "type": "plain_text",
                "text": "Custom Alert Format:\n {{ status_emoji }} [{{ status_text }}] {{ title }}",
                "emoji": true
              }
            }

            {
              "type": "section",
              "text": {
                "type": "mrkdwn",
                "text": "{{ status_emoji }} *[{{ status_text }}] {{ title }}*{% if mention %} {{ mention }}{% endif %}"
              }
            }

            {
              "type": "divider"
            }

            {
              "type": "section",
              "fields": [
                {
                  "type": "mrkdwn",
                  "text": "*Type:* {{ alert_type }}"
                },
                {
                  "type": "mrkdwn",
                  "text": "*Severity:* {{ severity_emoji }} {{ severity }}"
                },
                {
                  "type": "mrkdwn",
                  "text": "*Cluster:* {{ cluster_name }}"
                }
                {% if resource_text %}
                ,
                {
                  "type": "mrkdwn",
                  "text": "*Resource:*\\n{{ resource_text }}"
                }
                {% endif %}
              ]
            }

            {
              "type": "section",
              "text": {
                "type": "mrkdwn",
                "text": "{% if labels %}*Labels:*\\n\\n{% for key, value in labels.items() %}• *{{ key }}*: {{ value }}\\n\\n{% endfor %}{% else %}*Labels:* _None_{% endif %}"
              }
            }

Templates use Slack's Block Kit format and must generate valid JSON. Each template block is separated by double newlines (``\n\n``).

Available template variables:

+-----------------------------+-------------------------------------------------------------+
| Variable                    | Description                                                 |
+=============================+=============================================================+
| ``title``                   | The alert title                                             |
+-----------------------------+-------------------------------------------------------------+
| ``description``             | The alert description                                       |
+-----------------------------+-------------------------------------------------------------+
| ``status_text``             | "Firing" or "Resolved"                                      |
+-----------------------------+-------------------------------------------------------------+
| ``status_emoji``            | "⚠️" (for firing) or "✅" (for resolved)                    |
+-----------------------------+-------------------------------------------------------------+
| ``severity``                | Alert severity (e.g., "Warning", "Critical")                |
+-----------------------------+-------------------------------------------------------------+
| ``severity_emoji``          | Emoji for the severity level                                |
+-----------------------------+-------------------------------------------------------------+
| ``alert_type``              | "Alert", "K8s Event", or "Notification"                     |
+-----------------------------+-------------------------------------------------------------+
| ``cluster_name``            | The name of the cluster                                     |
+-----------------------------+-------------------------------------------------------------+
| ``investigate_uri``         | URI for investigation                                       |
+-----------------------------+-------------------------------------------------------------+
| ``resource_text``           | Resource identifier (e.g., "Pod/namespace/name")            |
+-----------------------------+-------------------------------------------------------------+
| ``subject_kind``            | The Kubernetes resource kind (e.g., "Pod", "Deployment")    |
+-----------------------------+-------------------------------------------------------------+
| ``subject_namespace``       | The Kubernetes namespace                                    |
+-----------------------------+-------------------------------------------------------------+
| ``subject_name``            | The name of the Kubernetes resource                         |
+-----------------------------+-------------------------------------------------------------+
| ``resource_emoji``          | Emoji for the resource type                                 |
+-----------------------------+-------------------------------------------------------------+
| ``mention``                 | Any @mentions extracted from the title                      |
+-----------------------------+-------------------------------------------------------------+
| ``labels``                  | Kubernetes labels on the subject resource (dict)            |
+-----------------------------+-------------------------------------------------------------+
| ``annotations``             | Kubernetes annotations on the subject resource (dict)       |
+-----------------------------+-------------------------------------------------------------+
| ``fingerprint``             | The unique identifier for the alert                         |
+-----------------------------+-------------------------------------------------------------+
