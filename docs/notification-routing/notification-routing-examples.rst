:hide-toc:

Routing Cookbook
===================================

.. toctree::
   :maxdepth: 1
   :hidden:

   routing-by-namespace
   routing-by-type
   implementing-monitoring-shifts
   routing-to-multiple-slack-channels
   routing-exclusion
   routing-by-severity
   excluding-resolved
   disable-oomkill-notifications

In this section you'll find example configurations for common routing patterns.


.. grid:: 1 1 2 3
    :gutter: 3

    .. grid-item-card:: :octicon:`book;1em;` Routing by Namespace
        :class-card: sd-bg-light sd-bg-text-light
        :link: routing-by-namespace
        :link-type: doc

        Route notifications based on Kubernetes namespaces.

    .. grid-item-card:: :octicon:`book;1em;` Routing by Alert Name
        :class-card: sd-bg-light sd-bg-text-light
        :link: routing-by-type
        :link-type: doc

        Route notifications based on alert types.

    .. grid-item-card:: :octicon:`book;1em;` Route by Time of Day
        :class-card: sd-bg-light sd-bg-text-light
        :link: implementing-monitoring-shifts
        :link-type: doc

        Implement monitoring shifts for better alert management.

    .. grid-item-card:: :octicon:`book;1em;` Routing to Multiple Slack Channels
        :class-card: sd-bg-light sd-bg-text-light
        :link: routing-to-multiple-slack-channels
        :link-type: doc

        Send notifications to multiple Slack channels.

    .. grid-item-card:: :octicon:`book;1em;` Routing Exclusion
        :class-card: sd-bg-light sd-bg-text-light
        :link: routing-exclusion
        :link-type: doc

        Exclude specific alerts from being routed.

    .. grid-item-card:: :octicon:`book;1em;` Dropping Specific Alerts
        :class-card: sd-bg-light sd-bg-text-light
        :link: routing-by-severity
        :link-type: doc

        Route notifications based on alert severity.

    .. grid-item-card:: :octicon:`book;1em;` Excluding "Resolved" Notifications
        :class-card: sd-bg-light sd-bg-text-light
        :link: excluding-resolved
        :link-type: doc

        Exclude resolved alerts from notifications.

    .. grid-item-card:: :octicon:`book;1em;` Disable "OOMKill" Notifications
        :class-card: sd-bg-light sd-bg-text-light
        :link: disable-oomkill-notifications
        :link-type: doc

        Disable notifications for OOMKill events.