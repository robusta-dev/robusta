Sinks
======

.. toctree::
   :hidden:
   :maxdepth: 1

   slack
   telegram
   discord
   kafka
   DataDog
   ms-teams
   mattermost
   webhook
   Opsgenie
   VictorOps
   PagerDuty

Playbooks results (findings) can be sent to one or more sinks (destinations). Findings will be automatically formatted in a way
that makes sense for each sink.

Supported sinks
^^^^^^^^^^^^^^^^^^^^^
The following sinks are supported:

.. grid:: 2
    :gutter: 3

    .. grid-item-card:: :octicon:`cpu;1em;` Slack
        :class-card: sd-bg-light sd-bg-text-light
        :link: slack
        :link-type: doc

        
    .. grid-item-card:: :octicon:`cpu;1em;` Telegram
        :class-card: sd-bg-light sd-bg-text-light
        :link: telegram
        :link-type: doc

   
    .. grid-item-card:: :octicon:`cpu;1em;` Discord
        :class-card: sd-bg-light sd-bg-text-light
        :link: discord
        :link-type: doc


    .. grid-item-card:: :octicon:`cpu;1em;` Kafka
        :class-card: sd-bg-light sd-bg-text-light
        :link: kafka
        :link-type: doc


    .. grid-item-card:: :octicon:`cpu;1em;` DataDog
        :class-card: sd-bg-light sd-bg-text-light
        :link: DataDog
        :link-type: doc

    .. grid-item-card:: :octicon:`cpu;1em;` MS-teams
        :class-card: sd-bg-light sd-bg-text-light
        :link: ms-teams
        :link-type: doc
    
    .. grid-item-card:: :octicon:`cpu;1em;` Mattermost
        :class-card: sd-bg-light sd-bg-text-light
        :link: mattermost
        :link-type: doc

    .. grid-item-card:: :octicon:`cpu;1em;` Webhook
        :class-card: sd-bg-light sd-bg-text-light
        :link: webhook
        :link-type: doc

    .. grid-item-card:: :octicon:`cpu;1em;` OpsGenie
        :class-card: sd-bg-light sd-bg-text-light
        :link: Opsgenie
        :link-type: doc

    .. grid-item-card:: :octicon:`cpu;1em;` VictorOps
        :class-card: sd-bg-light sd-bg-text-light
        :link: VictorOps
        :link-type: doc

    .. grid-item-card:: :octicon:`cpu;1em;` PagerDuty
        :class-card: sd-bg-light sd-bg-text-light
        :link: PagerDuty
        :link-type: doc


**Need support for something not listed here?** `Tell us and we'll add it to the code. <https://github.com/robusta-dev/robusta/issues/new?assignees=&labels=&template=feature_request.md&title=New%20Sink:>`_

See :ref:`Defining additional sinks` for more details

Sending Findings to Specific Sinks
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
A sink can be configured to receive only certain findings. For example, you can send notifications to different Slack channels depending on the namespace:

.. code-block:: yaml

    sinksConfig:
    - slack_sink:
        name: slack_app_sink
        slack_channel: app-notifications
        api_key: secret-key
        match:
          namespace:
          - app
    - slack_sink:
        name: slack_system_sink
        slack_channel: system-notifications
        api_key: secret-key
        match:
          namespace:
          - kube-system


See :ref:`Sink matchers` for more details.

Default sinks
^^^^^^^^^^^^^^^^^^
If a playbook doesn't specify a sink then output will be sent to the default sinks. A sink is considered default
if it has the field `default: true` in the YAML.

