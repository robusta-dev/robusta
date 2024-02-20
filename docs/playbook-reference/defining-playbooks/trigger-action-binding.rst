Matching Actions to Triggers
################################
Each trigger outputs an event of a specific type, and each action expects a typed event as input.

For example, the ``on_prometheus_alert`` trigger outputs a *PrometheusAlert* event, while ``on_pod_update`` outputs a *PodChangeEvent.*

These events flow into the actions section, where each action is compatible with a subset of event types.
For instance, the ``logs_enricher`` action expects to receive events that have a Pod object, such as *PrometheusAlert*, *PodEvent*, or *PodChangeEvent*.

When configuring Robusta playbooks you don't need to worry about all these details. You can just look at each trigger and see which actions are supported.

This page defines in-depth how triggers are bound to actions.

Simple actions
-----------------

Simple actions take no special parameters and can therefore run on every trigger.

Resource-related actions
--------------------------

Some actions require Kubernetes resources as input.

For example, the ``logs_enricher`` action requires a pod as input.

Therefore, ``logs_enricher`` can only be connected to triggers which output a pod. For example:

* ``on_pod_create``
* ``on_pod_update``
* ``on_prometheus_alert`` - for alerts with a ``pod`` label
* :ref:`manual trigger <Manual Triggers>` - by passing the pod's name as a cli argument

Trigger hierarchies
-------------------------------

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

Developer Guide
-----------------

If you extend Robusta with custom actions in Python, refer to :ref:`the developer guide <Events and Triggers>`.
