Kubernetes (API Server)
############################

.. _kubernetes_triggers:

Robusta can run automated playbooks when Kubernetes resources change. Playbooks can identify issues, track changes, or automate actions.

These triggers work even when Prometheus is not connected to Robusta. They're triggered by the Kubernetes APIServer directly.

.. details:: Related Tutorials

    * :ref:`Track Failed Kubernetes Jobs`
    * :ref:`Track Failed Liveness Probes`
    * :ref:`Track Kubernetes Changes`


Crashing Pod Triggers
------------------------

The following triggers are available for crashing Pods:

.. _on_pod_crash_loop:

.. details:: on_pod_crash_loop

    ``on_pod_crash_loop`` fires when a Pod is crash looping. It has the following parameters:

    * ``restart_reason``: Limit restart loops for this specific reason. If omitted, all restart reasons will be included.
    * ``restart_count``: Fire only after the specified number of restarts
    * ``rate_limit``: Limit firing to once every `rate_limit` seconds

    An example playbook using :ref:`report_crash_loop<report_crash_loop>` to show logs of crashing pods:

    .. code-block:: yaml

        customPlaybooks:
        - triggers:
          - on_pod_crash_loop:
              restart_reason: "CrashLoopBackOff"
          actions:
          - report_crash_loop: {}

.. _on_pod_oom_killed:

.. details:: on_pod_oom_killed

    ``on_pod_oom_killed`` fires when any container in a Pod is OOMKilled. It has the following parameters:

    * ``rate_limit``: Limit firing to once every `rate_limit` seconds
    * ``exclude``: A list of pod name prefixes and/or namespaces that this trigger will ignore.
        * All pods that start with `name` in namespace `namespace` will be ignored for this trigger.
        * If A `name` is defined without a `namespace` than all pods with that name prefix will be ignored for this trigger.
        * If A `namespace` is defined without a `name` than all pods in that namespace will be ignored for this trigger.


    An example playbook using :ref:`pod_graph_enricher<pod_graph_enricher>` to show memory graphs of OOMKilled Pods:

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

.. _on_container_oom_killed:

.. details:: on_container_oom_killed

    ``on_container_oom_killed`` fires when a Container is OOMKilled. It has the following parameters:

    * ``rate_limit``: Limit firing to once every `rate_limit` seconds
    * ``exclude``: A list of container name prefixes and/or namespaces that this trigger will ignore.
        * All containers that start with `name` in namespace `namespace` will be ignored for this trigger.
        * If A `name` is defined without a `namespace` than all containers with that name prefix will be ignored for this trigger.
        * If A `namespace` is defined without a `name` than all containers in that namespace will be ignored for this trigger.

    An example playbook using :ref:`oomkilled_container_graph_enricher<oomkilled_container_graph_enricher>`:

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


.. _on_image_pull_backoff:

.. details:: on_image_pull_backoff

    ``on_image_pull_backoff`` fires when a Pod has ImagePullBackoff state. It has the following parameters:

    * ``rate_limit``: Limit firing to once every `rate_limit` seconds
    * ``fire_delay``: Fire only if the pod is running for more than fire_delay seconds.
    * ``name_prefix``: Name of the pod (or a prefix of it)
    * ``namespace_prefix``: Namespace the pod is in (or a prefix of it)
    * ``labels_selector``: See :ref:`Common Filters`

    An example playbook using the :ref:`image_pull_backoff_reporter<image_pull_backoff_reporter>` action to gather details about the issue:

    .. code-block:: yaml

        customPlaybooks:
        - triggers:
          - on_image_pull_backoff: {}
          actions:
          - image_pull_backoff_reporter: {}


.. _on_pod_evicted:

.. details:: on_pod_evicted

    ``on_pod_evicted`` fires when a Pod has the evicted reason in its status. It has the following parameters:

    * ``rate_limit``: Limit firing to once every `rate_limit` seconds
    * ``name_prefix``: Name of the pod (or a prefix of it)
    * ``namespace_prefix``: Namespace the pod is in (or a prefix of it)
    * ``labels_selector``: See :ref:`Common Filters`
    * ``scope``: See :ref:`Common Filters`

    An example playbook:

    .. code-block:: yaml


        customPlaybooks:
        - triggers:
          - on_pod_evicted: {}
          actions:
          - create_finding: #
              title: "Pod $name in namespace $namespace was Evicted"
              aggregation_key: "PodEvictedTriggered"


For triggers that fire on any Pod change, see :ref:`Pod Triggers`.

Job Failure Triggers
------------------------

The following triggers are available for failed Jobs:

.. _on_job_failure:

.. details:: on_job_failure

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

For triggers that fire on any Job change, see :ref:`Job Triggers`.

Warning Event Triggers
------------------------

Warning events are the output of:

.. code-block::

    kubectl get events --all-namespaces --field-selector type=Warning

The following triggers track Warning Events:

.. jinja::
  :header_update_levels:
  :file: playbook-reference/triggers/_k8s-warning-events.jinja

.. admonition:: Which trigger should I use?

    You should almost always use the ``on_kubernetes_warning_event_create`` trigger. The other triggers are documented for completeness, but are rarely useful.

All Warning Event Triggers support optional *inclusion* and *exclusion* filters. These filters perform a text-match on
each the Event's reason and message fields. Matching is case insensitive.

Low-level Triggers
----------------------

Low-level triggers fire on the raw creation, deletion, and modification of resources in your cluster. They can be noisy
compared to other triggers, as they fire on even the smallest change to a resource.

Multi-Resource Triggers
-------------------------

.. _on_kubernetes_resource_operation:

.. details:: on_kubernetes_resource_operation

    ``on_kubernetes_resource_operation`` fires when one of the specified resources, had one of the specified operations.

    * ``operations``: List of `operations`. If empty, all `operations` are included. Options:
        * ``create``
        * ``update``
        * ``delete``
    * ``resources``: List of Kubernetes `resources`. If empty, all `resources` are included. Options:
        * ``deployment``
        * ``pod``
        * ``job``
        * ``node``
        * ``replicaset``
        * ``statefulset``
        * ``daemonset``
        * ``ingress``
        * ``service``
        * ``event``
        * ``horizontalpodautoscaler``
        * ``clusterrole``
        * ``clusterrolebinding``
        * ``namespace``
        * ``serviceaccount``
        * ``persistentvolume``
        * ``configmap``

    Example playbook:

    .. code-block:: yaml

        customPlaybooks:
        - triggers:
          - on_kubernetes_resource_operation:
              resources: ["deployment"]
              operations: ["update"]
          actions:
          - create_finding:
              title: "Deployment $name on namespace $namespace updated"
              aggregation_key: "Deployment Update"



Single Resource Triggers
-------------------------

.. jinja::
  :inline-ctx: { "resource_name" : "Pod", "related_actions" : ["Pod Enrichers (General)", "pod_events_enricher"] }
  :header_update_levels:
  :file: playbook-reference/triggers/_k8s-generic-triggers.jinja

For triggers that fire only on Pod errors, see :ref:`Crashing Pod Triggers`.

.. jinja::
  :inline-ctx: { "resource_name" : "ReplicaSet", "related_actions" : ["related_pods"] }
  :header_update_levels:
  :file: playbook-reference/triggers/_k8s-generic-triggers.jinja

.. jinja::
  :inline-ctx: { "resource_name" : "DaemonSet", "related_actions" : ["Daemonset Enrichers", "related_pods"] }
  :header_update_levels:
  :file: playbook-reference/triggers/_k8s-generic-triggers.jinja

.. jinja::
  :inline-ctx: { "resource_name" : "Deployment", "related_actions" : ["Deployment Enrichers", "deployment_events_enricher", "related_pods"] }
  :header_update_levels:
  :file: playbook-reference/triggers/_k8s-generic-triggers.jinja

.. jinja::
  :inline-ctx: { "resource_name" : "StatefulSet", "related_actions" : [] }
  :header_update_levels:
  :file: playbook-reference/triggers/_k8s-generic-triggers.jinja

.. jinja::
  :inline-ctx: { "resource_name" : "Service", "related_actions" : [] }
  :header_update_levels:
  :file: playbook-reference/triggers/_k8s-generic-triggers.jinja

.. jinja::
  :inline-ctx: { "resource_name" : "Ingress", "related_actions" : [] }
  :header_update_levels:
  :file: playbook-reference/triggers/_k8s-generic-triggers.jinja

.. jinja::
  :inline-ctx: { "resource_name" : "Event", "related_actions" : ["Event Enrichers"] }
  :header_update_levels:
  :file: playbook-reference/triggers/_k8s-generic-triggers.jinja

.. jinja::
  :inline-ctx: { "resource_name" : "HorizontalPodAutoscaler", "related_actions" : [] }
  :header_update_levels:
  :file: playbook-reference/triggers/_k8s-generic-triggers.jinja

.. jinja::
  :inline-ctx: { "resource_name" : "Node", "related_actions" : ["Node Enrichers", "related_pods"] }
  :header_update_levels:
  :file: playbook-reference/triggers/_k8s-generic-triggers.jinja

.. jinja::
  :inline-ctx: { "resource_name" : "ClusterRole", "related_actions" : [] }
  :header_update_levels:
  :file: playbook-reference/triggers/_k8s-generic-triggers.jinja

.. jinja::
  :inline-ctx: { "resource_name" : "ClusterRoleBinding", "related_actions" : [] }
  :header_update_levels:
  :file: playbook-reference/triggers/_k8s-generic-triggers.jinja

.. jinja::
  :inline-ctx: { "resource_name" : "Job", "related_actions" : ["Job Enrichers", "related_pods"] }
  :header_update_levels:
  :file: playbook-reference/triggers/_k8s-generic-triggers.jinja

.. jinja::
  :inline-ctx: { "resource_name" : "Namespace", "related_actions" : [] }
  :header_update_levels:
  :file: playbook-reference/triggers/_k8s-generic-triggers.jinja

.. jinja::
  :inline-ctx: { "resource_name" : "ServiceAccount", "related_actions" : [] }
  :header_update_levels:
  :file: playbook-reference/triggers/_k8s-generic-triggers.jinja

.. jinja::
  :inline-ctx: { "resource_name" : "PersistentVolume", "related_actions" : [] }
  :header_update_levels:
  :file: playbook-reference/triggers/_k8s-generic-triggers.jinja

.. jinja::
   :inline-ctx: { "resource_name": "Secret", "related_actions": [], "custom_description": "Secret triggers fire when secret resource changes. *By default Robusta does not support tracking secrets*, but you can enable it by :ref:`configuring kubewatch to monitor secrets<track-secrets-overview>`." }
   :header_update_levels:
   :file: playbook-reference/triggers/_k8s-generic-triggers.jinja



Wildcard triggers
*********************

Wildcard triggers fire when any supported Kubernetes resource changes. They are equivalent to a *union* of all other
low-level triggers.


.. jinja::
  :header_update_levels:
  :file: playbook-reference/triggers/_k8s-wildcard-triggers.jinja

Common Filters
-----------------

Most Kubernetes triggers support the following filters:

* ``name_prefix``
* ``namespace_prefix``
* ``labels_selector`` - e.g. ``label1=value1,label2=value2``. If multiple labels is provided, all must match.

Additionally, Kubernetes triggers support a ``scope`` filtering mechanism that works almost
exactly like the ``scope`` mechanism for sinks (see :ref:`sink-scope-matching` for more
information). The only difference is that for triggers, there is an additional option
available for the ``include``/``exclude`` sections, ``attributes``, that makes it possible
to filter on *any* attribute inside the YAML representation of the resource. An example
of use of this functionality:

.. code-block:: yaml

    customPlaybooks:
    - name: "FilteredPodCreation"
      triggers:
        - on_pod_create:
            scope:
              include:
                - name:
                  - my-pod.*
                  - other
                  namespace: ns1
                  labels:
                    - "foo=bar, boo=xx.*"
                    - "foo=xx, boo=xx.*"
                  attributes:
                    - "status.phase=Pending, status.qosClass=BestEffort, metadata.resourceVersion != 123"
                    - "spec.restartPolicy=OnFailure"
                  annotations:
                    - "foo=bar, boo=xx.*"
                    - "foo=xx, boo=xx.*"
              exclude:
                - name:
                  - woof.*

Note that ``attributes`` matching only allows exact equality and inequality. The left-hand side
of each of ``attributes`` filters is a path to select appropriate node in the document. It
supports typical constructs like following nested attributes using the ``.`` operator, or
selecting n-th element of a list using the ``[n]`` operator. In fact the language used to
describe paths is much more versatile, as the implementation uses ``jsonpath-ng`` under
the hood. You can read more about it `here <https://pypi.org/project/jsonpath-ng/>`_.
