Welcome to Robusta
================================

Robusta is a popular platform for Kubernetes monitoring and observability. It monitors what matters and shows you *why* alerts fired, what happened at the same time, and how to get things back to normal fast.

Robusta pulls together data from Prometheus, the Kubernetes API Server, and more. (See `comparison with bare-bones Prometheus <https://home.robusta.dev/prometheus-based-monitoring/?from=docs>`_.)

Some data Robusta gathers is trivial - for example, pod logs. Other data is complex - for example, `Java heap dumps <https://home.robusta.dev/java>`_.
In all cases, Robusta makes data *accessible* by showing it to the right people, exactly when they need it, in the most convenient place possible. (Slack, MS Teams, etc.)

Robusta is `open source <https://github.com/robusta-dev/robusta>`_.

Example Use Cases
~~~~~~~~~~~~~~~~~~

.. tab-set::

    .. tab-item:: Crashing pods

        .. admonition:: Monitor crashing pods and send their logs to Slack

            .. image:: /images/crash-report2.png
                :width: 700
                :align: center

    .. tab-item:: Event Correlation

        .. admonition:: Show application updates in Grafana to correlate them with error spikes

            .. image:: /images/grafana-deployment-enrichment.png
              :width: 400
              :align: center

    .. tab-item:: Remediate alerts

        .. admonition:: Temporarily increase the HPA maximum so you can go back to sleep

            .. image:: /images/alert_on_hpa_reached_limit1.png
                :width: 600
                :align: center

    .. tab-item:: Debug Pods

        .. admonition:: Attach the VSCode debugger to a running Python pod without tearing your hair out

            .. image:: /images/python-debugger.png
              :width: 600
              :align: center

            .. code-block:: bash

                 robusta playbooks trigger python_debugger name=podname namespace=default

            See :ref:`Python debugger` for more details

How it works
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The core of Robusta is an automations engine, somewhat like Zapier/IFTTT for DevOps.

For example, you can enrich an alert with pod logs (``kubectl logs``) and forward it to Slack:

.. code-block:: yaml

    triggers:
      - on_prometheus_alert:
          alert_name: KubePodCrashLooping
    actions:
      - logs_enricher: {}
    sinks:
      - slack

Every automation has three parts:

.. grid:: 3

    .. grid-item-card:: Triggers
        :class-card: sd-bg-light sd-bg-text-light
        :link: catalog/triggers/index
        :link-type: doc

        When to run
        (on alerts, logs, changes, etc)

    .. grid-item-card::  Actions
        :class-card: sd-bg-light sd-bg-text-light
        :link: catalog/actions/index
        :link-type: doc

        What to do
        (over 50 builtin actions)

    .. grid-item-card::  Sinks
        :class-card: sd-bg-light sd-bg-text-light
        :link: catalog/sinks/index
        :link-type: doc

        Where to send the result
        (Slack, etc)

.. image:: ./images/robusta_motion_graphics_transparent.gif
   :align: center

Writing your own automations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Many automations are included, but you can also write your own in Python.

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
                MarkdownBlock("*Oh no!* An alert occurred on " + pod_name),
                FileBlock("crashing-pod.log", pod_logs)
            ])

Why Robusta
~~~~~~~~~~~~

Everyone has a lot of observability data, but making sense of it requires deep knowledge.

It needs to be easier to do **the right thing** when receiving an alert. Specifically:

1. It should be easier to investigate an alert then ignore it
2. It should never take more than 5 minutes to understand *why* an alert fired
3. Silencing false positives should take one click

By harnessing runbook automation and **community knowledge** we are building a rulebook of all common Kubernetes issues, root causes, and fixes.

Next Steps
~~~~~~~~~~~~

:ref:`Ready to install Robusta? Get started! <installation>`

`Star us on GitHub to receive updates. <https://github.com/robusta-dev/robusta/>`_

.. toctree::
   :hidden:

   Project Home <https://home.robusta.dev/?from=docs>

.. toctree::
   :maxdepth: 4
   :caption: About Robusta
   :hidden:

   Overview <self>
   architecture
   coverage
   community
   oss-vs-saas


.. toctree::
   :maxdepth: 4
   :caption: Tutorials
   :hidden:

   installation
   tutorials/configuring-automations
   tutorials/prometheus-enrichment
   tutorials/my-first-custom-action
   tutorials/python-profiling
   tutorials/java-troubleshooting
   tutorials/more-tutorials

..
   tutorials/alert-correlation

.. toctree::
   :maxdepth: 4
   :caption: Reference
   :hidden:

   upgrade
   common-errors
   user-guide/configuration
   user-guide/flow-control
   catalog/triggers/index
   catalog/actions/index
   catalog/sinks/index
   user-guide/robusta-cli
   user-guide/trigger-action-binding
   advanced/index

.. toctree::
   :maxdepth: 4
   :caption: Developer Guide
   :hidden:

   developer-guide/actions/index
   developer-guide/platform/index
