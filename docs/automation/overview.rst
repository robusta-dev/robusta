:hide-toc:
Overview
======================

Robusta is a Kubernetes monitoring platform with **strong automation capabilities**.

Automations have three main use cases:

* Listening to the Kubernetes API Server and generating alerts
* Gathering observability data when alerts fire - e.g. logs, graphs, thread dumps
* Automatically remediating alerts with runbook automation

Conceptually, the automations engine is similar to Zapier/IFTTT but built for devops scenarios and defined in YAML. Automations are event-triggered.

Examples
------------------
Lets take a Prometheus alert for crashing pods and automate the process of fetching pod logs. The result will be sent to Slack.

.. code-block:: yaml

    triggers:
      - on_prometheus_alert:
          alert_name: KubePodCrashLooping
    actions:
      - logs_enricher: {}
    sinks:
      - slack

How Automations Work
----------------------

Every automation has three parts:

.. grid:: 1 1 2 3

    .. grid-item-card:: Triggers
        :class-card: sd-bg-light sd-bg-text-light
        :link: triggers/index
        :link-type: doc

        When to run
        (on alerts, logs, changes, etc)

    .. grid-item-card::  Actions
        :class-card: sd-bg-light sd-bg-text-light
        :link: actions/index
        :link-type: doc

        What to do
        (over 50 builtin actions)

    .. grid-item-card::  Sinks
        :class-card: sd-bg-light sd-bg-text-light
        :link: sinks/index
        :link-type: doc

        Where to send the result
        (Slack, etc)

Built-in automations
-----------------------
Robusta includes pre-defined automations that gather observability data about common errors.

