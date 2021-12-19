Welcome to Robusta!
=====================
Robusta is the best way to stay on top of Kubernetes alerts. It is an open source platform for automated troubleshooting
and maintenance.

Examples
~~~~~~~~~~~~~~~~~~

.. tab-set::

    .. tab-item:: Crashing pods

        .. admonition:: Example

            .. image:: /images/crash-report2.png
                :width: 700
                :align: center

            When a pod crashes, fetch the logs and send a message to Slack.

            This is configured by default, so after installing Robusta it just works. If you configured it yourself,
            it would look like this:

            .. code-block:: yaml

                triggers:
                  - on_prometheus_alert:
                      alert_name: KubePodCrashLooping
                actions:
                  - logs_enricher: {}
                sinks:
                  - slack

    .. tab-item:: Change tracking

        .. admonition:: Example

            .. image:: /images/grafana-deployment-enrichment.png
              :width: 400
              :align: center

            Write annotations to Grafana showing when applications are updated.

            Configure it like this:

            .. code-block:: yaml

                triggers:
                  - on_deployment_update: {}
                actions:
                  - add_deployment_lines_to_grafana:
                      grafana_url: <grafana_url>
                      grafana_api_key: <grafana_api_key>
                      grafana_dashboard_uid: <which_grafana_dashboard_to_update>

    .. tab-item:: Alert insights

        .. admonition:: Example

            .. image:: /images/node-cpu-alerts-enrichment.png
                :width: 30 %
                :alt: Analysis of node cpu usage, breakdown by pods
            .. image:: /images/node-cpu-usage-vs-request.svg
                :width: 30 %

            When a node has high CPU usage, analyze the node and provide actionable advice.

            This is configured by default, so after installing Robusta it just works. If you configured it yourself,
            it would look like this:

            .. code-block:: yaml

                triggers:
                  - on_prometheus_alert:
                      alert_name: HostHighCpuLoad
                actions:
                  - node_cpu_enricher: {}
                  - node_bash_enricher:
                      bash_command: "ps aux"
                sinks:
                  - slack

    .. tab-item:: Cloud debugging

        .. admonition:: Example

            Robusta can save time with manual troubleshooting too.

            Run this command to attach a Python profiler to a running pod:

            .. code-block:: bash

                 robusta playbooks trigger python_debugger name=myapp namespace=default process_substring=main

            You will get follow up instructions in Slack:

            .. image:: /images/python-debugger.png
              :width: 600
              :align: center

How it works
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You configure automations in a three-part yaml:

.. grid:: 3

    .. grid-item-card:: Triggers
        :class-card: sd-bg-light
        :link: catalog/triggers/index
        :link-type: doc

        When to run
        (on alerts, logs, changes, etc)

    .. grid-item-card::  Actions
        :class-card: sd-bg-light
        :link: catalog/actions/index
        :link-type: doc

        What to do
        (over 50 builtin actions)

    .. grid-item-card::  Sinks
        :class-card: sd-bg-light
        :link: catalog/sinks/index
        :link-type: doc

        Where to send the result
        (Slack, etc)

Why Robusta
~~~~~~~~~~~

Robusta makes troubleshooting automated, reproducible, and open source.

It turns expert knowledge into re-usable code so that you can:

* Respond to incidents in a reproducible manner
* Track changes and identify regressions
* See out-of-the-box insights for common alerts
* Automatically silence false alarms
* Fix alerts in one click from Slack or the terminal

:ref:`Robusta has over 50 builtin actions. <Actions>` and can be extended in Python:

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


Architecture
~~~~~~~~~~~~~~~~~~~~
Robusta can be used as

.. dropdown:: A complete Kubernetes monitoring stack
    :color: light

    Robusta will install a bundled Prometheus stack. Includes:

    * Robusta automations engine + builtin automations
    * Prometheus, AlertManager, and Grafana
    * Out of the box alerts fine-tuned for Kubernetes

.. dropdown:: An automations engine for your existing stack
    :color: light

    Robusta will integrate with external tools like your existing Prometheus, Datadog, or Elasticsearch. Includes:

    * Robusta automations engine + builtin automations

Next Steps
~~~~~~~~~~~~

:ref:`Ready to install Robusta? Get started! <Installation Guide>`

Still not convinced? See `the demos on our website <http://startup.natanyellin.com/>`_.

.. toctree::
   :hidden:

   self

.. toctree::
   :maxdepth: 4
   :caption: Getting Started
   :hidden:

   getting-started/installation
   getting-started/example-playbook
   getting-started/manual-triggers
   getting-started/support

.. toctree::
   :maxdepth: 4
   :caption: Automation Catalog
   :hidden:

   catalog/triggers/index
   catalog/actions/index
   catalog/sinks/index

.. toctree::
   :maxdepth: 4
   :caption: User Guide
   :hidden:
   :glob:

   user-guide/configuration
   user-guide/upgrade
   user-guide/robusta-cli
   user-guide/architecture

.. toctree::
   :maxdepth: 4
   :caption: Developer Guide
   :hidden:

   developer-guide/writing-playbooks
   developer-guide/findings-api
   developer-guide/triggers-and-events
   developer-guide/general-guidelines