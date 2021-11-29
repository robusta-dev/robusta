Welcome to Robusta!
=====================
Robusta is the best way to stay on top of Kubernetes alerts. It monitors events and triggers automated responses.

Features:

* Add missing context to Prometheus alerts and filter out false alarms
* Reduce the volume of flooded alert channels with prebuilt fixes
* Monitor changes to Kubernetes resources
* Benefit from open source playbooks written by other companies

You can use Robusta as:

.. dropdown:: A complete Kubernetes monitoring stack
    :color: light

    Robusta will install a bundled Prometheus stack including:

    * Prometheus, AlertManager, and Grafana
    * Out of the box alerts fine-tuned for Kubernetes

.. dropdown:: An automations engine for your existing stack
    :color: light

    Robusta will run automations in response to your existing alerts.

    Supports Prometheus, Datadog, Elasticsearch, and more.

    Robusta will **not** install Prometheus or other tools.

How it works
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You configure triggers and actions in YAML.

For example, you can configure Robusta to gather logs when a pod crashes:

.. code-block:: yaml

    - triggers:
      - on_prometheus_alert:
          alert_name: KubePodCrashLooping
      actions:
      - logs_enricher: {}

Results are sent to Slack, MSTeams, or other destinations:

.. image:: /images/crash-report.png
    :width: 700
    :align: center

There are over 50 builtin actions you can use.

If you know Python, you can write your own playbook actions like the ``logs_enricher`` used above.

.. dropdown:: View example action
    :color: light

    .. code-block:: python

        # this action runs on triggers you define in the YAML
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

Concepts
~~~~~~~~~~~~~~~~~~~~
Robusta was inspired by three good ideas from other domains:

1. Automated tests make finding bugs a continuous and unavoidable process
2. Infrastructure as code makes complicated workflows reproducible
3. Package managers like Helm share operational knowledge via open source

**Robusta makes troubleshooting automated, reproducible, and open source**.

More examples
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Here are some common things people automate with Robusta:

* Send logs of crashing pods to Slack/MSTeams
* Enrich ``HostOutOfDiskSpace`` alerts with details about large files
* Enrich all alerts with diffs of recently changed deployments
* Attach a CPU profiler for 2 seconds on ``HighCPU`` without restarting your application
* Track and audit every change in a Kubernetes cluster
* Increase max replicas from Slack during an incident

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