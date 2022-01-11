Triggers
==========

This page describes the events that can trigger Robusta automations.

If you are new to Robusta, see :ref:`the tutorial <Example Playbook>` first.

Builtin triggers
^^^^^^^^^^^^^^^^^^

You can trigger Robusta actions on all of the following events:

.. toctree::
   :maxdepth: 1

   Prometheus and AlertManager alerts <prometheus>
   Changes to Kubernetes Resources <kubernetes>
   ElasticSearch Monitors <elasticsearch>
   Scheduled events <scheduled>
   External webhooks <webhook>
   Manual triggers <../../getting-started/manual-triggers.rst>

Trigger-action compatibility
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Some actions require Kubernetes resources as input and can only run on compatible triggers.

For example, the ``logs_enricher`` action requires a pod as input. It can only be connected to triggers which output a
pod such as:

* ``on_pod_create``
* ``on_pod_update``
* ``on_prometheus_alert`` - for alerts with a ``pod`` label
* :ref:`manual trigger <Manual Triggers>` - by passing the pod's name as a cli argument

Where possible, trigger-action compatibility is checked when Robusta loads its config. Feel free to experiment though.
Incompatible triggers and actions will fail gracefully with a warning.

How triggers pass data to actions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Each trigger loads data about the incoming event. This data is passed as a Python object to the action.

Trigger hierarchy
^^^^^^^^^^^^^^^^^^^^^^^^^

All of the triggers in Robusta form a hierarchy. If a playbook supports a specific trigger, it also supports
descendants of that trigger.

For example, the trigger ``on_deployment_all_changes`` has a child trigger ``on_deployment_create``.
So the latter may be used wherever the former is expected.

.. graphviz::

    digraph trigger_inheritance {
        bgcolor=transparent;
        rankdir=LR;
        size="8.0, 12.0";
        node [fillcolor=white,fontname="Vera Sans, DejaVu Sans, Liberation Sans, Arial, Helvetica, sans",fontsize=10,height=0.25,shape=box,style="setlinewidth(0.5),filled"]
        "on_schedule";
        "on_prometheus_alert";
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
