:hide-toc:
Overview
===========
Robusta can be modified to cater your needs. Write custom playbooks or improve the built in playbooks.

Writing your own automations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Many automations are included, but you can also write your own in Python.

.. details:: View example action (Python)

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
                MarkdownBlock("*Oh no!* An alert occurred on " + pod_name),
                FileBlock("crashing-pod.log", pod_logs)
            ])


Developement guides
^^^^^^^^^^^^^^^^^^^
.. grid:: 1 1 2 3
    :gutter: 3

    .. grid-item-card:: :octicon:`cpu;1em;` Implement a custom sink
        :class-card: sd-bg-light sd-bg-text-light
        :link: /extending/platform/sinks-guide
        :link-type: doc

        Add a new destination for your alerts

        
    .. grid-item-card:: :octicon:`cpu;1em;` Custom playbook repositories
        :class-card: sd-bg-light sd-bg-text-light
        :link: /extending/actions/index
        :link-type: doc

        Create your own playbook repositories

   
    .. grid-item-card:: :octicon:`cpu;1em;` Docs contributions
        :class-card: sd-bg-light sd-bg-text-light
        :link: /extending/platform/docs-contributions
        :link-type: doc

        Learn to setup a local docs developement environment