Welcome to Robusta!
=====================
Robusta is the best way to stay on top of Kubernetes alerts. It monitors incoming alerts and triggers automated
responses.

Features:

* Add missing context to Prometheus alerts and filter out false alarms
* Reduce the volume of flooded alert channels with prebuilt fixes
* Monitor changes to Kubernetes resources
* Benefit from open source playbooks written by other companies

How it works
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You configure triggers and actions in YAML:

.. admonition:: Example Configuration

    .. code-block:: yaml

        - triggers:
          - on_prometheus_alert:
              alert_name: HostOutOfDiskSpace
          actions:
          - node_bash_enricher:
              bash_command: "df -h"


Results are sent to Slack, MSTeams, or other destinations:

.. admonition:: Example Slack Message

    .. image:: /images/crash-report.png

You can write your own playbook actions in Python:

.. admonition:: Example Action

    .. code-block:: python

        @action
        def my_action(alert: PrometheusKubernetesAlert):
            print(f"The alert {alert.alert_name} fired on pod {alert.pod.metadata.name}")
            print(f"The pod has these processes:", alert.pod.exec("ps aux"))
            print(f"The pod has {len(alert.pod.spec.containers)} containers")



Concepts
~~~~~~~~~~~~~~~~~~~~
Robusta was inspired by three good ideas from other domains:

1. Automated tests make finding bugs a continuous and unavoidable process
2. Infrastructure as code makes complicated workflows reproducible
3. Package managers like Helm share operational knowledge via open source

**Robusta makes troubleshooting automated, reproducible, and open source**.

More examples
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Here are common Robusta automations:

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
