Triggers
==========

This page describes the events that can trigger Robusta automations.

If you are new to Robusta, see :ref:`the tutorial <Example Playbook>` first.

Builtin triggers
^^^^^^^^^^^^^^^^^^

.. toctree::
   :maxdepth: 1

   prometheus
   kubernetes
   elasticsearch
   scheduled
   webhook

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
