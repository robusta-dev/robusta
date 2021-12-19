Welcome to Robusta!
=====================
Robusta is the best way to stay on top of Kubernetes alerts. It is an open source platform for automated troubleshooting
and maintenance.

Use Cases
~~~~~~~~~~~

* Respond to incidents in a reproducible manner
* Track changes and identify regressions
* See out-of-the-box insights for common alerts
* Automatically silence false alarms
* Fix alerts in one click from Slack or the terminal

Robusta can be used as:

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


How it works
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You configure automations in a three-part yaml:

triggers:
    When to run

actions:
    What to do

sinks:
    Where to send the result

Examples
~~~~~~~~~~~~~~~~~~

.. tab-set::

    .. tab-item:: Crashing pods

        .. admonition:: Example: monitor crashing pods

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

            .. image:: /images/crash-report.png
                :width: 700
                :align: center

    .. tab-item:: Grafana Annotations

        .. admonition:: Example: show updates in Grafana

            Write annotations to Grafana showing when applications were updated.

            No sink is configured. This action writes directly to Grafana and no output is sent to sinks.

            .. code-block:: yaml

                triggers:
                  - on_deployment_update: {}
                actions:
                  - add_deployment_lines_to_grafana:
                      grafana_url: <grafana_url>
                      grafana_api_key: <grafana_api_key>
                      grafana_dashboard_uid: <which_grafana_dashboard_to_update>

            .. image:: /images/grafana-deployment-enrichment.png
              :width: 400
              :align: center

    .. tab-item:: HighCPU alerts

        .. admonition:: Example: show insights on HighCPU Usage

            When a node has high CPU usage, analyze the node and provide actionable advice. Also run ``ps aux`` on the
            node.

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

            .. image:: /images/node-cpu-alerts-enrichment.png
                :width: 30 %
                :alt: Analysis of node cpu usage, breakdown by pods
            .. image:: /images/node-cpu-usage-vs-request.svg
                :width: 30 %

    .. tab-item:: Change Tracking

        .. admonition:: Example: track deployment updates

            This notifies in Slack when ``status.conditions`` is modified for a Deployment

            .. code-block:: yaml

                triggers:
                  - on_deployment_update: {}
                actions:
                  - resource_babysitter:
                      fields_to_monitor: ["status.conditions"]
                sinks:
                  - slack

            .. image:: /images/deployment-babysitter.png
              :width: 600
              :align: center

More examples:

* See what changed before an alert fired
* Track and audit changes in a cluster
* Apply workarounds from Slack like scaling up Deployments
* Monitor and fix health issues like low disk space
* Debug high CPU by profiling for 2 seconds without restarting your application


Motivation
~~~~~~~~~~~~~~~~~~~~

**Robusta makes troubleshooting automated, reproducible, and open source**.

The Robusta vision is to freely share all devops knowledge and best-practices.

With Robusta, all companies can identify and troubleshoot problems like experts because
Robusta turns expert knowledge into re-usable code.

Features
~~~~~~~~~~~~~~~~~~~~

.. dropdown:: Supported triggers
    :color: light

    * Prometheus alerts
    * Elasticsearch monitors
    * Changes to Kubernetes resources
    * Log lines written by applications


.. dropdown:: Supported actions
    :color: light

    * Fetch a pod's logs
    * Run a bash command on a pod
    * Run a bash command on a node
    * Attach a CPU profiler for X seconds
    * More than 50 additional actions
    * Easy to add your own actions

.. dropdown:: Supported sinks
    :color: light

    * Slack
    * MSTeams (beta)
    * Datadog
    * Kafka
    * Robusta UI
    * Open a Github issue requesting support for a new sink

Extending Robusta
~~~~~~~~~~~~~~~~~~~
If you know Python, you can extend Robusta with your own actions.

.. dropdown:: View example action
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

See the :ref:`builtin playbooks <List of built-in playbooks>` or write your own.

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
   :caption: User Guide
   :hidden:
   :glob:

   user-guide/configuration
   user-guide/upgrade
   user-guide/robusta-cli
   user-guide/architecture

.. toctree::
   :maxdepth: 4
   :caption: Reference
   :hidden:

   reference/triggers/index
   reference/actions/index
   reference/sinks/index


.. toctree::
   :maxdepth: 4
   :caption: Developer Guide
   :hidden:

   developer-guide/writing-playbooks
   developer-guide/general-guidelines
   developer-guide/reference
   developer-guide/findings-api