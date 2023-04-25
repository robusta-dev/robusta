Kubernetes (API Server)
############################

.. _kubernetes_triggers:

Robusta can run automated playbooks when Kubernetes resources change.

Example Use Cases
-------------------

* :ref:`Track Failed Kubernetes Jobs`
* :ref:`Track Failed Liveness Probes`
* :ref:`Track Kubernetes Changes`

High-Level Triggers
--------------------------

These triggers fire on *interesting events*. Internally, they are implemented on top of :ref:`Low-Level Triggers`

Warning Event Triggers
************************

These triggers fire when Kubernetes Warning Events are modified:

.. _on_kubernetes_warning_event_create:
.. _on_kubernetes_warning_event_update:
.. _on_kubernetes_warning_event_delete:
.. _on_kubernetes_warning_event:

* ``on_kubernetes_warning_event_create``
* ``on_kubernetes_warning_event_update``
* ``on_kubernetes_warning_event_delete``
* ``on_kubernetes_warning_event``

As clarification, Warning events are the output of:

.. code-block::

    kubectl get events --all-namespaces --field-selector type=Warning

All Warning Event Triggers support optional *inclusion* and *exclusion* filters. These filters perform a text-match on
each the Event's reason and message fields. Matching is case insensitive.

An exclusion filter:

.. code-block:: yaml

   - triggers:
     - on_kubernetes_warning_event_create:
         exclude: ["NodeSysctlChange", "TooManyPods"]

An inclusion filter:

.. code-block:: yaml

   - triggers:
     - on_kubernetes_warning_event_create:
         include: ["ImagePullBackOff"]

Crashing Pod Triggers
**********************

Several triggers are available for crashing Pods:

* :ref:`on_pod_crash_loop<on_pod_crash_loop>`
* :ref:`on_container_oom_killed<on_container_oom_killed>`
* :ref:`on_pod_oom_killed<on_pod_oom_killed>`

on_pod_crash_loop
^^^^^^^^^^^^^^^^^^^

``on_pod_crash_loop`` fires when a Pod is crash looping. It has the following parameters:

* ``restart_reason``: Limit restart loops for this specific reason. If omitted, all restart reasons will be included.
* ``restart_count``: Fire only after the specified number of restarts
* ``rate_limit``: Limit firing to once every `rate_limit` seconds

An example playbook:

.. code-block:: yaml

    customPlaybooks:
    - triggers:
      - on_pod_crash_loop:
          restart_reason: "CrashLoopBackOff"
      actions:
      - report_crash_loop: {}

on_pod_oom_killed
^^^^^^^^^^^^^^^^^^^^^^^^^

``on_pod_oom_killed`` fires when any container in a Pod is OOMKilled.

.. code-block:: yaml

    customPlaybooks:
    - triggers:
      - on_pod_oom_killed:
          rate_limit: 900
          exclude:
            - name: "oomkilled-pod"
              namespace: "default"
      actions:
      - pod_graph_enricher:
          resource_type: Memory
          display_limits: true

Trigger Parameters:

* ``rate_limit``: Limit firing to once every `rate_limit` seconds
* ``exclude``: A list of pod name prefixes and/or namespaces that this trigger will ignore.
    * All pods that start with `name` in namespace `namespace` will be ignored for this trigger.
    * If A `name` is defined without a `namespace` than all pods with that name prefix will be ignored for this trigger.
    * If A `namespace` is defined without a `name` than all pods in that namespace will be ignored for this trigger.

on_container_oom_killed
^^^^^^^^^^^^^^^^^^^^^^^^^

``on_container_oom_killed`` fires when a Container is OOMKilled.

.. code-block:: yaml

    customPlaybooks:
    - triggers:
      - on_container_oom_killed:
          rate_limit: 900
          exclude:
            - name: "oomkilled-container"
              namespace: "default"
      actions:
      - oomkilled_container_graph_enricher:
          resource_type: Memory

Trigger parameters:

* ``rate_limit``: Limit firing to once every `rate_limit` seconds
* ``exclude``: A list of container name prefixes and/or namespaces that this trigger will ignore.
    * All containers that start with `name` in namespace `namespace` will be ignored for this trigger.
    * If A `name` is defined without a `namespace` than all containers with that name prefix will be ignored for this trigger.
    * If A `namespace` is defined without a `name` than all containers in that namespace will be ignored for this trigger.


Job Triggers
***************

on_job_failure
^^^^^^^^^^^^^^^^^^

``on_job_failure`` fires when a Job's status is updated to "failed".

Example playbook:

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


Low-level Triggers
----------------------

Low-level triggers fire on the raw creation, deletion, and modification of resources in your cluster. Compared to
:ref:`High-Level Triggers` they can be noisy.

Prefer using :ref:`High-Level Triggers` when possible, and open an
`issue <https://github.com/robusta-dev/robusta/issues/new?assignees=&labels=&template=other.md&title=>`_
on GitHub if you need a new high-level trigger.

Low-Level Filters
***********************

All low-level triggers support the following filters:

* ``name_prefix`` - Name prefix to match resources.
* ``namespace_prefix`` - Namespace prefix to match resources.
* ``labels_selector`` - Match resources with these labels. The format is: ``label1=value1,label2=value2``. If more than one labels is provided, **all** need to match.

TODO: do all Kubernetes triggers support these, including high-level triggers?

Wildcard triggers
*********************

Wildcard triggers fire when any supported Kubernetes resource changes. They are equivalent to a *union* of all other
low-level triggers.

* on_kubernetes_any_resource_create
* on_kubernetes_any_resource_update
* on_kubernetes_any_resource_delete
* on_kubernetes_any_resource_all_changes


.. jinja:: autogen_triggers
   :header_update_levels:
   :file: configuration/defining-playbooks/triggers/_k8s-trigger.jinja
