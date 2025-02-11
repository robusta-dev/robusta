:hide-toc:

Actions Reference
==================

.. toctree::
   :maxdepth: 1
   :hidden:

   message-formatting
   event-enrichment
   remediation
   change-tracking
   networking
   grafana
   scans
   miscellaneous
   develop-actions/index

Robusta can take many automated actions, in response to events in your cluster.

Built-in Actions
-----------------------

.. grid:: 1 1 2 2
    :gutter: 3

    .. grid-item-card:: :octicon:`cpu;1em;` Message Formatting
        :class-card: sd-bg-light sd-bg-text-light
        :link: message-formatting
        :link-type: doc

    .. grid-item-card:: :octicon:`cpu;1em;` Event Enrichment
        :class-card: sd-bg-light sd-bg-text-light
        :link: event-enrichment
        :link-type: doc

    .. grid-item-card:: :octicon:`cpu;1em;` Remediation
        :class-card: sd-bg-light sd-bg-text-light
        :link: remediation
        :link-type: doc

    .. grid-item-card:: :octicon:`cpu;1em;` Change Tracking
        :class-card: sd-bg-light sd-bg-text-light
        :link: change-tracking
        :link-type: doc

    .. grid-item-card:: :octicon:`cpu;1em;` Grafana
        :class-card: sd-bg-light sd-bg-text-light
        :link: grafana
        :link-type: doc

    .. grid-item-card:: :octicon:`cpu;1em;` Scans
        :class-card: sd-bg-light sd-bg-text-light
        :link: scans
        :link-type: doc

    .. grid-item-card:: :octicon:`cpu;1em;` Miscellaneous
        :class-card: sd-bg-light sd-bg-text-light
        :link: miscellaneous
        :link-type: doc

Custom Actions
---------------

Need to do something that the builtin actions don't cover? :ref:`Write your own Robusta action in Python.<Developing New Actions>`

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
