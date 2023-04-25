Creating Notifications
######################

Playbooks can generate notifications to *let a human know* about something in your cluster.

A *Finding* is Robusta's term for a notification.

This guide explains how to create and modify Findings in :ref:`customPlaybooks <customPlaybooks>`.

Actions for Working with Findings
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

There are two generic actions for working with notifications:

* :ref:`create_finding<create_finding>`
* :ref:`customise_finding<customise_finding>`

``create_finding`` will generate a new notification.

``customise_finding`` will modify an existing notification, already created by other actions.

For example, we can use ``create_finding`` to notify about failed Jobs.

.. code-block:: yaml

    customPlaybooks:
    - triggers:
      - on_job_failure:
          namespace_prefix: robusta
      actions:
      - create_finding:
          title: "Job $name on namespace $namespace failed"
          aggregation_key: "Job Failure"

TODO: show screenshot.

Adding Details to Notifications
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Robusta's true power is the ability to build *detailed* and *context-aware* notifications.

For example, if a Kubernetes Job fails, we can lookup the last Pod to run inside the Job, fetch it's logs, and attach
those logs to the notification:

TODO show example

Details Are Always Inside Findings
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Actions can add details to a notification, even if a notification wasn't created first.

When this occurs, a new notification will be implicitly created with a default title and description. You can then
override the default notification using :ref:`customise_finding<customise_finding>`. Alternatively, you can insert
a :ref:`create_finding<create_finding>` action before adding details. These two methods are equivalent.

Some actions both create notifications and attach details. For instance, ``report_crash_loop`` generates a
notification and also attaches logs.

The Order of Actions Matters
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. note::

    This section is going to change in the future. We're planning to simplify the Findings API so it's even easier to
    use.

The order of actions within a playbook is important. Some actions create notifications. Other actions attach data to
existing notification. Make sure actions that create notifications run first. Otherwise you will receive multiple
notifications.

