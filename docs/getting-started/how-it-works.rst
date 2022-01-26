How it works
##################

Robusta automates everything that happens **after** you deploy your application.

It is somewhat like Zapier/IFTTT for devops, with an emphasis on prebuilt automations and not just "build your own".

Concepts
~~~~~~~~~~~~

You configure automations in a three-part yaml:

.. grid:: 3

    .. grid-item-card:: Triggers
        :class-card: sd-bg-light sd-bg-text-light
        :link: ../catalog/triggers/index
        :link-type: doc

        When to run
        (on alerts, logs, changes, etc)

    .. grid-item-card::  Actions
        :class-card: sd-bg-light sd-bg-text-light
        :link: ../catalog/actions/index
        :link-type: doc

        What to do
        (over 50 builtin actions)

    .. grid-item-card::  Sinks
        :class-card: sd-bg-light sd-bg-text-light
        :link: ../catalog/sinks/index
        :link-type: doc

        Where to send the result
        (Slack, etc)

Automations run via webhook so if they fail it wont bring down your environment.

Writing your own actions
--------------------------

Many actions are included, but you can also write your own in Python.

.. dropdown:: View example action (Python)
    :color: light

    .. code-block:: python

        # this runs on Prometheus alerts you specify in the YAML
        @action
        def my_enricher(event: PrometheusKubernetesAlert):
            # we have full access to the pod on which the alert fired
            pod = event.get_pod()
            pod_name = pod.metadata.name
            pod_logs = pod.get_logs()
            pod_processes = pod.exec("ps aux")

            # this is how you send data to slack or other destinations
            event.add_enrichment([
                MarkdownBlock("*Oh no!* An alert occurred on " + pod_name)
                FileBlock("crashing-pod.log", pod_logs)
            ])



Components
~~~~~~~~~~~~~~~~~~~

Robusta has several components:

A Python framework for writing better webhooks and automations
    Robusta handles the plumbing so you can focus on the logic.

50+ prebuilt webhooks and automations for common actions
    No need to write code. Just enable these with YAML.

An opinionated Prometheus configuration (optional)
    Don't configure anything. It just works. Better alerts + insights.

`A better frontend for AlertManager <https://home.robusta.dev/ui/>`_ (optional)
    We put your existing alerts on a timeline and let you slice and dice them. You gain visibility into
    Kubernetes changes that occurred before an alert fired. And more.
