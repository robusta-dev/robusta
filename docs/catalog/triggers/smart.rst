Smart Triggers
############################

.. _smart_triggers:

Robusta actions can run in response to some decision logic.

Example triggers
------------------
Pod Crash Loop
^^^^^^^^^^^^^^^^^^^

* ``on_pod_crash_loop``

This trigger will fire when a Pod is crash looping.

Trigger parameters:

* ``restart_reason``: Limit restart loops for this specific reason. If omitted, all restart reasons will be included.
* ``restart_count``: Fire only after the specified number of restarts
* ``rate_limit``: Limit firing to once every `rate_limit` seconds

.. code-block:: yaml

    customPlaybooks:
    - triggers:
      - on_pod_crash_loop:
          restart_reason: "CrashLoopBackOff"
      actions:
      - report_crash_loop: {}



.. note::

    Have an idea for another smart trigger? Please open a github `issue <https://github.com/robusta-dev/robusta/issues>`_
