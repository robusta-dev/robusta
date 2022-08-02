Smart Triggers
############################

.. _smart_triggers:

These high-level triggers identify interesting events in your cluster.

| Under the hood, smart triggers are implemented on top of lower-level triggers.
| For example, the `on_pod_crash_loop` trigger internally listens to other :ref:`Kubernetes (API Server)` triggers and applies logic to fire only on crashing pods.


Example triggers
------------------
Pod Crash Loop
^^^^^^^^^^^^^^^^^^^

.. _on_pod_crash_loop:

* ``on_pod_crash_loop``

This trigger will fire when a Pod is crash looping.


.. code-block:: yaml

    customPlaybooks:
    - triggers:
      - on_pod_crash_loop:
          restart_reason: "CrashLoopBackOff"
      actions:
      - report_crash_loop: {}


Trigger parameters:

* ``restart_reason``: Limit restart loops for this specific reason. If omitted, all restart reasons will be included.
* ``restart_count``: Fire only after the specified number of restarts
* ``rate_limit``: Limit firing to once every `rate_limit` seconds

Pod OOMKilled
^^^^^^^^^^^^^^^^^^^

.. _on_container_oom_killed:

* ``on_container_oom_killed``

This trigger will fire when a container is OOMKilled.


.. code-block:: yaml

    customPlaybooks:
    - triggers:
      - on_container_oom_killed: {}
      actions:
      - pod_graph_enricher:
          resource_type: Memory
          display_limits: true


Trigger parameters:

* ``rate_limit``: Limit firing to once every `rate_limit` seconds

Job Failure
^^^^^^^^^^^^^^^^^^^

.. _on_job_failure:

* ``on_job_failure``

This trigger will fire when the Job status is updated to "failed".


.. code-block:: yaml

    customPlaybooks:
    - triggers:
      - on_job_failure:
          namespace_prefix: robusta
      actions:
      - create_finding:
          title: "Job $name on namespace $namespace failed"
          aggregation_key: "Job Failure"
      - job_events_enricher: { }


.. note::

    Have an idea for another smart trigger? Please open a github `issue <https://github.com/robusta-dev/robusta/issues/new?assignees=&labels=&template=other.md&title=>`_
