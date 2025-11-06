Playbook Notifications
######################

Playbooks can generate notifications to *let a human know* about something in your cluster.

A *Finding* is Robusta's term for a notification.

This guide explains how to create and modify *Findings* in :ref:`customPlaybooks <customPlaybooks>`.

Creating Notifications
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

There are two generic actions for working with notifications:

* :ref:`create_finding<create_finding>`
* :ref:`customise_finding<customise_finding>`

``create_finding`` will generate a new notification.

``customise_finding`` will modify an existing notification, already created by other actions.

For example, we can use ``create_finding`` to notify about Pods that were killed because they used up memory.

.. code-block:: yaml

    customPlaybooks:
    - triggers:
      - on_pod_oom_killed: {} # (1)
      actions:
      - create_finding:
          title: "Pod $name in namespace $namespace OOMKilled results"
          aggregation_key: "Pod OOMKill"

.. code-annotations::
    1. See :ref:`on_pod_oom_killed<on_pod_oom_killed>`

Enriching Notifications
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Robusta's true power is the ability to build *detailed* and *context-aware* notifications.

Lets use these capabilities to improve the above example. When a Pod is OOMKilled, we usually investigate by:

1. Viewing a graph of Pod memory usage
2. Running ``kubectl describe`` and investigating

We can automate this with Robusta:

.. code-block:: yaml

    customPlaybooks:
    - triggers:
      - on_pod_oom_killed: {} # (1)
      actions:
      - create_finding:
          title: "Pod $name in namespace $namespace OOMKilled results"
          aggregation_key: "Pod OOMKill"
      - pod_graph_enricher: # (2)
          resource_type: Memory
          display_limits: true
      - pod_oom_killer_enricher: {} # (3)

.. code-annotations::
    1. See :ref:`on_pod_oom_killed<on_pod_oom_killed>`
    2. See :ref:`pod_graph_enricher<pod_graph_enricher>`
    3. See :ref:`pod_oom_killer_enricher<pod_oom_killer_enricher>`
    4. See :ref:`mention_enricher<mention_enricher>`

Here is the result in Slack:

.. image:: /images/oomkill-notification-with-enrichers.png

.. admonition:: What's the difference between actions and enrichers?

    Enrichers are just regular Robusta actions. :ref:`Learn more. <actions-vs-enrichers-vs-silencers>`

Automatic Findings
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

What happens if you call an enrichment action like ``pod_graph_enricher`` but you never call ``create_finding`` first?

No worries. In cases like this, a default Finding (notification) is created when the enricher runs. The Finding's title
is set automatically based on the event that triggered the action.

This means that the order of actions within a playbook is important! Put ``create_finding`` before other actions, so that subsequent actions
already have a Finding to work with. If you put ``pod_graph_enricher`` before ``create_finding``, you'll end up with
two notification messages - one created implicitly by calling ``pod_graph_enricher`` and one created
explicitly by ``create_finding``.

.. note::

    Some actions both create Findings and enrich them. For instance, :ref:`report_crash_loop<report_crash_loop>` does both.
    In this case, there's no need to call ``create_finding`` explicitly.
