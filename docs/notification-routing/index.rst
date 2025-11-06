:hide-toc:

Notifications & Routing Overview
=================================

Robusta can send notifications to various destinations and route them intelligently based on alert type, namespace, severity, and more.

Key Concepts
^^^^^^^^^^^^

:doc:`Sinks <../configuration/sinks/index>` - Destinations where notifications are sent (Slack, Teams, Email, etc.)

:doc:`Routing <routing-with-scopes>` - Rules that determine which alerts go to which sinks

:doc:`Grouping <notification-grouping>` - Thread alerts together to reduce noise (especially in Slack)

:doc:`Silencing <routing-silencing>` - Temporarily disable specific notifications

Getting Started
^^^^^^^^^^^^^^^

.. grid:: 1 1 2 2
    :gutter: 3

    .. grid-item-card:: Configure Sinks
        :class-card: sd-bg-light sd-bg-text-light
        :link: configuring-sinks
        :link-type: doc

        Start here - learn how to set up your first notification destination

    .. grid-item-card:: Popular Sinks
        :class-card: sd-bg-light sd-bg-text-light
        :link: ../configuration/sinks/slack
        :link-type: doc

        Slack, Teams, Email - quick setup for common destinations

    .. grid-item-card:: Smart Routing
        :class-card: sd-bg-light sd-bg-text-light
        :link: routing-with-scopes
        :link-type: doc

        Send different alerts to different teams automatically

    .. grid-item-card:: Reduce Noise
        :class-card: sd-bg-light sd-bg-text-light
        :link: notification-grouping
        :link-type: doc

        Group related alerts in Slack threads to avoid spam

Popular Sinks
^^^^^^^^^^^^^

.. grid:: 1 1 2 4
    :gutter: 2

    .. grid-item-card:: Slack
        :class-card: sd-bg-light sd-bg-text-light
        :link: ../configuration/sinks/slack
        :link-type: doc

    .. grid-item-card:: Teams
        :class-card: sd-bg-light sd-bg-text-light
        :link: ../configuration/sinks/ms-teams
        :link-type: doc

    .. grid-item-card:: PagerDuty
        :class-card: sd-bg-light sd-bg-text-light
        :link: ../configuration/sinks/PagerDuty
        :link-type: doc

    .. grid-item-card:: View All Sinks
        :class-card: sd-bg-light sd-bg-text-light
        :link: ../configuration/sinks/index
        :link-type: doc