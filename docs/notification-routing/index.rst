:hide-toc:

Notifications & Routing Overview
=================================

Robusta can send notifications to various destinations and route them intelligently based on alert type, namespace, severity, and more.

Key Concepts
^^^^^^^^^^^^

**Sinks** - Destinations where notifications are sent (Slack, Teams, Email, etc.)

**Routing** - Rules that determine which alerts go to which sinks

**Grouping** - Thread alerts together to reduce noise (especially in Slack)

**Silencing** - Temporarily disable specific notifications

Getting Started
^^^^^^^^^^^^^^^

.. grid:: 1 1 2 2
    :gutter: 3

    .. grid-item-card:: :octicon:`gear;1em;` Configure Sinks
        :class-card: sd-bg-light sd-bg-text-light
        :link: configuring-sinks
        :link-type: doc

        Start here - learn how to set up your first notification destination

    .. grid-item-card:: :octicon:`mail;1em;` Popular Sinks
        :class-card: sd-bg-light sd-bg-text-light
        :link: ../configuration/sinks/slack
        :link-type: doc

        Slack, Teams, Email - quick setup for common destinations

    .. grid-item-card:: :octicon:`workflow;1em;` Smart Routing
        :class-card: sd-bg-light sd-bg-text-light
        :link: routing-with-scopes
        :link-type: doc

        Send different alerts to different teams automatically

    .. grid-item-card:: :octicon:`comment-discussion;1em;` Reduce Noise
        :class-card: sd-bg-light sd-bg-text-light
        :link: notification-grouping
        :link-type: doc

        Group related alerts in Slack threads to avoid spam

Common Workflows
^^^^^^^^^^^^^^^^

**Basic Setup**: Configure a single sink (like Slack) to receive all notifications

**Team Routing**: Route alerts to different channels based on namespace or labels

**Noise Reduction**: Enable grouping and silencing for cleaner notifications

**Advanced Routing**: Use scopes and filters for complex routing scenarios

Next Steps
^^^^^^^^^^

1. **Configure Your First Sink** - Start with :doc:`configuring-sinks`
2. **Choose Your Destination** - Browse all available sinks in :doc:`../configuration/sinks/index`
3. **Set Up Routing** - Configure intelligent routing with :doc:`routing-with-scopes`
4. **Reduce Noise** - Enable grouping with :doc:`notification-grouping`