Welcome to Robusta!
=====================
Robusta is the best way to stay on top of Kubernetes alerts. It is an open source platform for automated troubleshooting
and maintenance.

Use Cases
~~~~~~~~~~~

* Response to incidents in an automated and reproducible manner
* Out-of-the-box insights for common alerts
* Automatically flag known false alarms
* Track changes to Kubernetes resources and identify regressions
* Reduce alert fatigue with out-of-the-box playbooks
* Activate fixes from Slack or the terminal

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

Triggers:
    When this automation should run.

Actions:
    What the automation should do

Sinks:
    Where the result should be sent

Examples
~~~~~~~~~~~~~~~~~~

.. tab-set::

    .. tab-item:: Crashing pods

        .. admonition:: Send logs of crashing pods to Slack

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


    .. tab-item:: Deployment updates

        .. admonition:: Notify in Slack when deployments are updated

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

    .. tab-item:: HighCPU alerts

        .. admonition:: Send insights to Slack on high cpu usage. Also run ``ps aux`` on the relevant node.

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

    .. tab-item:: Grafana Annotations

        .. admonition:: Write annotations to Grafana when deployments are updated

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

Here are more things people automate with Robusta:

* Send logs of crashing pods to Slack/MSTeams
* Enrich all alerts with diffs of recently changed deployments
* Track and audit every change in a Kubernetes cluster
* Increase max replicas from Slack during an incident
* Enrich ``HostOutOfDiskSpace`` alerts with details about large files
* Attach a CPU profiler for 2 seconds on ``HighCPU`` without restarting your application


Inspiration
~~~~~~~~~~~~~~~~~~~~

Robusta was inspired by three good ideas from other domains:

1. Automated testing taught us the power of **automation**
2. Infrastructure as Code (IAC) made us love **reproducible** workflows
3. Helm showed us the power of **open source** communities

**Robusta makes troubleshooting automated, reproducible, and open source**.

Features
~~~~~~~~~~~~~~~~~~~~

.. dropdown:: Supported triggers
    :color: light

    * Prometheus alerts
    * Datadog alerts
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
   getting-started/customization
   getting-started/manual-triggers
   getting-started/more-commands

.. toctree::
   :maxdepth: 4
   :caption: User Guide
   :hidden:
   :glob:

   user-guide/builtin-playbooks
   user-guide/alerts
   user-guide/playbook-configuration
   user-guide/architecture

.. toctree::
   :maxdepth: 4
   :caption: Integrations
   :hidden:

   integrations/slack
   integrations/prometheus
   integrations/elasticsearch

.. toctree::
   :maxdepth: 4
   :caption: Developer Guide
   :hidden:

   developer-guide/writing-playbooks
   developer-guide/general-guidelines
   developer-guide/scheduled-playbooks
   developer-guide/reference
   developer-guide/findings-api