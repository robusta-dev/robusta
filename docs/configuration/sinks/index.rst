.. _sinks-reference:

:hide-toc:

All Sinks
==================


.. admonition:: Sinks are a legacy feature of Robusta classic
   :class: warning

   For new setups, we recommend `HolmesGPT <https://holmesgpt.dev/>`_ instead.

   HolmesGPT triages your alerts instead of just forwarding them. Sinks are deterministic: they send every notification, unchanged, to a fixed destination, leaving you to read and prioritize each one yourself.

   HolmesGPT instead uses AI to investigate each alert, surface the likely root cause, and escalate only what needs attention — so you get fewer, more actionable notifications. Set this up with `Alerts Triage <https://platform.robusta.dev/holmes/alerts-triage>`_ for alerts, or :ref:`Triggered Workflows <defining-playbooks>` for custom events.

Robusta can send notifications to various destinations, known as sinks.

**Related Topics:**

* :ref:`sinks-overview`
* :ref:`sink-scope-matching`

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

    .. grid-item-card:: :octicon:`cpu;1em;` ServiceNow
        :class-card: sd-bg-light sd-bg-text-light
        :link: ServiceNow
        :link-type: doc

    .. grid-item-card:: :octicon:`cpu;1em;` Zulip
        :class-card: sd-bg-light sd-bg-text-light
        :link: zulip
        :link-type: doc

**Need support for a new sink?** `Tell us and we'll add it. <https://github.com/robusta-dev/robusta/issues/new?assignees=&labels=&template=feature_request.md&title=New%20Sink:>`_

You can also :ref:`add the sink yourself <Developing a New Sink>` and open a PR.
