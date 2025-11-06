.. _customPlaybooks:
.. _Playbook Basics:

Playbooks Basics
##################

Playbooks are deterministic rules for responding to alerts and unhealthy conditions in a Kubernetes cluster.

Playbooks are recommended for advanced use cases. Most users should start with :doc:`AI Analysis </configuration/holmesgpt/main-features>` of alerts first, which requires far less configuration.

How Playbooks Work
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Every playbook consists of two parts:

* A :ref:`Trigger <Triggers Reference>` condition that defines when the automation runs
* An :ref:`Action <Actions Reference>` that defines what the automation does

Playbooks behave like pipelines:

1. Events come into Robusta and are checked against triggers
2. When there is a match, a trigger fires
3. The relevant playbook runs
4. All playbook actions execute, receiving the event as context
5. If :ref:`notifications <Playbook Notifications>` were generated, they are sent to :ref:`sinks <sinks-overview>`

Defining Custom Playbooks
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Using a custom playbook, we can get notified in Slack whenever a Pod's Liveness probe fails.

Use the ``customPlaybooks`` Helm value:

.. code-block:: yaml

    customPlaybooks:
    - triggers:
        - on_kubernetes_warning_event_create:
            include: ["Liveness"]   # fires on failed Liveness probes
      actions:
        - create_finding:
            severity: HIGH
            title: "Failed liveness probe: $name"
        - event_resource_events: {}

Perform a :ref:`Helm Upgrade <Simple Upgrade>` to apply the custom playbook.

Next time a Liveness probe fails, you will get notified.

    .. image:: /images/failedlivenessprobe.png
        :alt: Failing Kubernetes liveness probe notification on Slack
        :align: center

Apply the following command the simulate a failing liveness probe.

.. code-block:: yaml

    kubectl apply -f https://raw.githubusercontent.com/robusta-dev/kubernetes-demos/main/liveness_probe_fail/failing_liveness_probe.yaml


Let's explore each part of the above playbook in depth.

Using Filters to Restrict Triggers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Many triggers have parameters that restrict when they fire:

.. code-block:: yaml

    - triggers:
      - on_pod_crash_loop:
          restart_reason: "CrashLoopBackOff"
          name_prefix: fluentbit
          namespace_prefix: kube-system

Most Kubernetes-related triggers support at least ``name`` and ``namespace``. Refer to :ref:`Triggers Reference` for details.

Running Multiple Playbooks
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If multiple triggers match an incoming event, all relevant playbooks execute in the order they were defined. For example:

.. code-block:: yaml

   # first playbook
   - triggers:
     - on_deployment_create: {}
     actions:
     - my_first_action: {}

   # second playbook
   - triggers:
     - on_deployment_create: {}
     actions:
     - my_second_action: {}

In the example above, ``my_first_action`` runs before ``my_second_action``.

You can enable identical playbooks multiple times with different parameters:

.. code-block:: yaml

    customPlaybooks:
    - triggers:
      - on_deployment_update:
          name_prefix: MyApp
      actions:
      - add_deployment_lines_to_grafana:
          grafana_api_key: grafana_key_goes_here
          grafana_dashboard_uid: id_for_dashboard1
          grafana_url: http://grafana.namespace.svc

    - triggers:
      - on_deployment_update:
          name_prefix: OtherApp
      actions:
      - add_deployment_lines_to_grafana:
          grafana_api_key: grafana_key_goes_here
          grafana_dashboard_uid: id_for_dashboard2
          grafana_url: http://grafana.namespace.svc

If the triggers in multiple playbooks match the same incoming event, all relevant playbooks will run.

Understanding Triggers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Triggers** are event-driven, firing at specific moments when something occurs in your cluster. Even a Kubernetes cluster doing nothing generates a constant stream of events. Using triggers, you can find and react to the events that matter.

Going back to the above example, we saw the trigger ``on_kubernetes_warning_event_create``.
Breaking down the name, you'll notice the format ``on_<resource_type>_<operation>``. This is a general pattern.
``on_kubernetes_warning_event_create`` fires when new Warning Events (``kubectl get events --all-namespaces --field-selector type=Warning``) are created.

The trigger also had an *include* filter, limiting which Warning Events cause the playbook to run. In this case its a Liveness probe event.
See each trigger's documentation to learn which filters are supported.

Common Triggers
********************************
Popular triggers include:

* :ref:`on_prometheus_alert<on_prometheus_alert>`
* :ref:`on_pod_crash_loop<on_pod_crash_loop>`
* :ref:`on_deployment_update<on_deployment_update>`

All triggers can be found under :ref:`Triggers Reference`.

Understanding Actions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Actions** perform tasks in response to triggers, such as collecting information, investigating issues, or fixing problems.

In the above example, there were two actions. When playbooks contain multiple actions, they are executed in order:

* ``create_finding`` - this generates the notification message
* ``event_resource_events`` - this is a specific action for ``on_kubernetes_warning_event_create`` which attaches relevant events to the notification

The latter action has a funny name, which reflects that it takes a Kubernetes Warning Event as input, finds the related Kubernetes
resource (e.g. a Pod), and then fetches all the related Kubernetes Warning Events for that resource.

.. _actions-vs-enrichers-vs-silencers:

.. admonition:: Actions, Enrichers, and Silencers

    Many actions in Robusta were written for a specific purpose, like *enriching* alerts or *silencing* them.

    By convention, these actions are called *enrichers* and *silencers*, but those names are just convention.

    Under the hood, enrichers and silencers are plain old actions, nothing more.

Common Actions
********************************
Popular actions include:

* :ref:`logs_enricher<logs_enricher>` - fetch a Pod's logs
* :ref:`node_bash_enricher<node_bash_enricher>` - run a bash command on a Node
* :ref:`pod_bash_enricher<pod_bash_enricher>` - run a bash command on a Pod
* :ref:`pod_graph_enricher<pod_graph_enricher>` - attach a graph of Pod memory/CPU/disk usage

All actions can be found under :ref:`Actions Reference`.

Understanding Notifications
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In Robusta, notifications are called Findings, as they represent something the playbook discovered.

In the above example, a Finding was generated by the ``create_finding`` action. Refer to :ref:`Playbook Notifications`
for more details.

.. _Matching Actions to Triggers:

Matching Actions to Triggers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Each trigger outputs an event of a specific type, and each action expects a typed event as input.

For example, the ``on_prometheus_alert`` trigger outputs a *PrometheusAlert* event, while ``on_pod_update`` outputs a *PodChangeEvent*.

These events flow into the actions section, where each action is compatible with a subset of event types.
For instance, the ``logs_enricher`` action expects to receive events that have a Pod object, such as *PrometheusAlert*, *PodEvent*, or *PodChangeEvent*.

When configuring Robusta playbooks you don't need to worry about all these details. You can just look at each trigger and see which actions are supported.

Simple Actions
********************************

Simple actions take no special parameters and can therefore run on every trigger.

Resource-Related Actions
********************************

Some actions require Kubernetes resources as input.

For example, the ``logs_enricher`` action requires a pod as input.

Therefore, ``logs_enricher`` can only be connected to triggers which output a pod. For example:

* ``on_pod_create``
* ``on_pod_update``
* ``on_prometheus_alert`` - for alerts with a ``pod`` label
* :ref:`manual trigger <Manual Triggers>` - by passing the pod's name as a cli argument

Trigger Hierarchies
********************************

All of the triggers in Robusta form a hierarchy. If an action supports a specific trigger, it also supports
descendants of that trigger.

For example, the trigger ``on_deployment_all_changes`` has a child trigger ``on_deployment_create``.
The latter may be used wherever the former is expected.

.. graphviz::

    digraph trigger_inheritance {
        bgcolor=transparent;
        rankdir=LR;
        size="8.0, 12.0";
        node [fillcolor=white,fontname="Vera Sans, DejaVu Sans, Liberation Sans, Arial, Helvetica, sans",fontsize=10,height=0.25,shape=box,style="setlinewidth(0.5),filled"]
        "on_schedule";
        "on_prometheus_alert**";
        "on_kubernetes_any_resource_all_changes";
        "on_deployment_all_changes";
        "on_deployment_create";
        "on_deployment_update";
        "on_deployment_delete";
        "on_deployment_all_changes" -> "on_deployment_create" [arrowsize=0.5,style="setlinewidth(0.5)"];
        "on_deployment_all_changes" -> "on_deployment_update" [arrowsize=0.5,style="setlinewidth(0.5)"];
        "on_deployment_all_changes" -> "on_deployment_delete" [arrowsize=0.5,style="setlinewidth(0.5)"];
        "on_kubernetes_any_resource_all_changes" -> "on_deployment_all_changes" [arrowsize=0.5,style="setlinewidth(0.5)"];
    }

.. note::

    ``on_prometheus_alert`` is compatible with most Robusta actions that take Kubernetes resources.

For more details, refer to :ref:`Actions Reference` to see which events each action supports. If you extend Robusta with custom actions in Python, refer to :ref:`the developer guide <Events and Triggers>`.

Modifying Default Playbooks
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

By default, Robusta has a default set of ``playbooks`` configured. These are used to create notifications for all common Kubernetes issues and Prometheus alerts.

You can disable any of the ``default playbooks``, or change the configuration of a given ``playbook``.

In order to disable a default playbook, add the playbook name to the ``disabledPlayooks`` helm value (Playbook name is in the ``name`` attribute of each playbook)

For example, to disable the ``ImagePullBackOff`` playbook, use:

.. code-block:: yaml

    disabledPlaybooks:
    - ImagePullBackOff

In order to override the default configuration of the same playbook, both disable it, and add it to ``customPlaybooks`` with the override configuration:

.. code-block:: yaml

    disabledPlaybooks:
    - ImagePullBackOff

    customPlaybooks:
    - name: "CustomImagePullBackOff"
      triggers:
      - on_image_pull_backoff:
          fire_delay: 300  # fire only if failing to pull the image for 5 min
      actions:
      - image_pull_backoff_reporter: {}


Organizing Playbooks
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Using ``namedCustomPlaybooks``, you can define playbooks by name. This is useful when you want to define a base set of playbooks for all clusters/teams and then use additional Helm values files to override some of the base playbooks or add new ones.

They are all merged together into a single playbooks list. This allows you to split away the custom playbooks from ``generated_values.yaml`` to separate files and organize your playbooks.

First, add the custom playbooks as a dictionary into a file named ``app_a_playbooks.yaml`` as shown below:


.. code-block:: yaml

    namedCustomPlaybooks:
    team-a-app-a:
      - triggers:
          - on_prometheus_alert:
              namespace_prefix: "app-a"
        actions:
          - create_finding:
              aggregation_key: "This is app-a - Requires your attention"
              severity: HIGH
              title: "Check app-a out"
              description: "@monitoring.monitoring this is for you"
    team-b-app-b:
      - triggers:
          - on_prometheus_alert:
              namespace_prefix: "app-b"
        actions:
          # Actions for team-b-app-b here

Then run a Helm upgrade by passing the new file using the ``-f`` flag.

.. code-block:: yaml

    helm ugprade --install robusta -f generated_values.yaml -f app_a_playbooks.yaml

Global Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To avoid repeating parameters across multiple playbooks, define them globally. These parameters will be applied to any action or trigger that expects a parameter with the same name.

For example, instead of repeating ``grafana_api_key`` and ``grafana_url``:

.. code-block:: yaml

   globalConfig:
     cluster_name: "my-staging-cluster"
     grafana_api_key: "grafana_key_goes_here"
     grafana_url: http://grafana.namespace.svc

    customPlaybooks:
    - triggers:
      - on_deployment_update:
          name_prefix: MyApp
      actions:
      - add_deployment_lines_to_grafana:
          grafana_dashboard_uid: id_for_dashboard1

    - triggers:
      - on_deployment_update:
          name_prefix: OtherApp
      actions:
      - add_deployment_lines_to_grafana:
          grafana_dashboard_uid: id_for_dashboard2
