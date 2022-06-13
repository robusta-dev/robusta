Trigger-Action Compatibility
################################

This page defines in-depth how triggers are bound to actions.

We're working on improving this documentation.
Please `open an issue on Github <https://github.com/robusta-dev/robusta/issues/new?assignees=&labels=&template=other.md&title=>`_ about anything that is unclear.

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

Error handling
-----------------

Where possible, trigger-action compatibility is checked when Robusta loads its config, so feel free to experiment.
Incompatible triggers and actions will fail gracefully with a warning.

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

Further Reading
-----------------
The way this works under the hood is explained on the :ref:`Events and Triggers` page.
