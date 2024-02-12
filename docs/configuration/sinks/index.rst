.. _sinks-reference:

:hide-toc:

Sinks Reference
==================

.. toctree::
   :hidden:
   :maxdepth: 1

   slack
   ms-teams
   RobustaUI
   mail
   telegram
   discord
   DataDog
   mattermost
   Opsgenie
   PagerDuty
   VictorOps
   YandexMessenger
   jira
   webhook
   file
   webex
   kafka
   rocketchat
   google_chat
   pushover
   sinks-development


Robusta can report issues and events in your Kubernetes cluster to various destinations, known as sinks.

By default, Robusta sends all notifications to all sinks.

**Related Topics:**

* :ref:`sinks-overview`
* :ref:`Routing Alerts to Specific Sinks`

Available sinks
^^^^^^^^^^^^^^^^^^^^^
Click a sink for setup instructions.

.. grid:: 1 1 2 3
    :gutter: 3

    .. grid-item-card:: :octicon:`cpu;1em;` Slack
        :class-card: sd-bg-light sd-bg-text-light
        :link: slack
        :link-type: doc

    .. grid-item-card:: :octicon:`cpu;1em;` MS-teams
        :class-card: sd-bg-light sd-bg-text-light
        :link: ms-teams
        :link-type: doc

    .. grid-item-card:: :octicon:`cpu;1em;` Robusta UI
        :class-card: sd-bg-light sd-bg-text-light
        :link: RobustaUI
        :link-type: doc

    .. grid-item-card:: :octicon:`cpu;1em;` Telegram
        :class-card: sd-bg-light sd-bg-text-light
        :link: telegram
        :link-type: doc

    .. grid-item-card:: :octicon:`cpu;1em;` Discord
        :class-card: sd-bg-light sd-bg-text-light
        :link: discord
        :link-type: doc

    .. grid-item-card:: :octicon:`cpu;1em;` DataDog
        :class-card: sd-bg-light sd-bg-text-light
        :link: DataDog
        :link-type: doc

    .. grid-item-card:: :octicon:`cpu;1em;` Mattermost
        :class-card: sd-bg-light sd-bg-text-light
        :link: mattermost
        :link-type: doc

    .. grid-item-card:: :octicon:`cpu;1em;` OpsGenie
        :class-card: sd-bg-light sd-bg-text-light
        :link: Opsgenie
        :link-type: doc

    .. grid-item-card:: :octicon:`cpu;1em;` PagerDuty
        :class-card: sd-bg-light sd-bg-text-light
        :link: PagerDuty
        :link-type: doc

    .. grid-item-card:: :octicon:`cpu;1em;` VictorOps
        :class-card: sd-bg-light sd-bg-text-light
        :link: VictorOps
        :link-type: doc

    .. grid-item-card:: :octicon:`cpu;1em;` Yandex Messenger
        :class-card: sd-bg-light sd-bg-text-light
        :link: YandexMessenger
        :link-type: doc

    .. grid-item-card:: :octicon:`cpu;1em;` Jira
        :class-card: sd-bg-light sd-bg-text-light
        :link: jira
        :link-type: doc

    .. grid-item-card:: :octicon:`cpu;1em;` Webhook
        :class-card: sd-bg-light sd-bg-text-light
        :link: webhook
        :link-type: doc

    .. grid-item-card:: :octicon:`cpu;1em;` File
        :class-card: sd-bg-light sd-bg-text-light
        :link: file
        :link-type: doc

    .. grid-item-card:: :octicon:`cpu;1em;` Webex
        :class-card: sd-bg-light sd-bg-text-light
        :link: webex
        :link-type: doc

    .. grid-item-card:: :octicon:`cpu;1em;` Kafka
        :class-card: sd-bg-light sd-bg-text-light
        :link: kafka
        :link-type: doc

    .. grid-item-card:: :octicon:`cpu;1em;` Rocket.Chat
        :class-card: sd-bg-light sd-bg-text-light
        :link: rocketchat
        :link-type: doc

    .. grid-item-card:: :octicon:`cpu;1em;` Mail
        :class-card: sd-bg-light sd-bg-text-light
        :link: mail
        :link-type: doc

    .. grid-item-card:: :octicon:`cpu;1em;` Google Chat
        :class-card: sd-bg-light sd-bg-text-light
        :link: google_chat
        :link-type: doc

    .. grid-item-card:: :octicon:`cpu;1em;` Pushover
        :class-card: sd-bg-light sd-bg-text-light
        :link: pushover
        :link-type: doc

**Need support for a new sink?** `Tell us and we'll add it. <https://github.com/robusta-dev/robusta/issues/new?assignees=&labels=&template=feature_request.md&title=New%20Sink:>`_

You can also :ref:`add the sink yourself <Developing a New Sink>` and open a PR.
