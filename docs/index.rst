Welcome to Robusta!
=====================
Robusta is the best way to respond to alerts in Kubernetes clusters. It automates the process of tracking,
investigating, and fixing production issues. To get started, just install Robusta and enable builtin
troubleshooting playbooks for common problems.

Common Use Cases
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Using Robusta you can automatically:

* See the largest files on a node when a ``HostOutOfDiskSpace`` Prometheus alert fires
* See which Kubernetes resources were updated prior to a Prometheus alert firing
* Safely run a CPU profiler for 2 seconds in production on high-cpu alerts
* Share manual troubleshooting workflows with colleagues as code and not outdated wiki pages
* Add annotations to Grafana graphs showing when applications were updated
* Track and audit every change in a Kubernetes cluster
* Enrich Prometheus alerts with pod logs and forward them to Slack/MSTeams
* Verify that application updates didn't cause a regression in top-line metrics
* Apply temporary workarounds to your cluster during an incident like increasing HPA max replicas

Robusta turns all the above maintenance operations into re-usable playbooks. See the :ref:`list of builtin playbooks <List of built-in playbooks>` or write your own.

The Core Concept
~~~~~~~~~~~~~~~~~~~~
Robusta is based on three principles:

1. **Automation improves software quality while saving time.** This is the reason automated testing exists.
Without automation you wouldn't test as frequently or as thoroughly, letting bugs creep through the cracks.
Robusta lets you handle alerts the same way you test software: via easy automation that you configure once and
run frequently.

2. **Automation makes complicated workflows reproducible by everyone.** This is the key principle of
infrastructure-as-code. Setting up servers manually leads to inconsistent results that are
hard to reproduce. It also creates knowledge silos where only certain individuals can setup new servers.
Responding to alerts manually in production is the same. We built Robusta to apply the principles of
infrastructure-as-code to alert handling.

3. **Your environment is not unique**. This is the reason why companies in different industries can
use the same Helm charts, install the same software, and have the same alerts in production. Robusta provides
out of the box playbooks for responding to those common issues with well-known best practices.


How it works
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Robusta installs two lightweight deployments in your Kubernetes cluster. The `forwarder` monitors
the cluster for changes and the `runner` uses your Robusta configuration file to decide when to run
playbooks.


.. image:: images/arch.png
   :width: 650


Playbooks can be sourced from the Robusta open source community or written by you in Python.
Configuring playbooks looks like this:


.. admonition:: Example Configuration

    .. code-block:: yaml

        - triggers:
          - on_prometheus_alert:
              alert_name: HostHighCpuLoad
          actions:
          - node_bash_enricher:
              bash_command: "df -h"

``on_prometheus_alert`` is a builtin *trigger* and ``node_bash_enricher`` is a builtin *action*.
Writing your own action in Python is as simple as this:

.. admonition:: Example Action

    .. code-block:: python

        @action
        def my_action(alert: PrometheusKubernetesAlert):
            print(f"The alert {alert.alert_name} fired on pod {alert.pod.metadata.name}")
            print(f"The pod has these processes:", alert.pod.exec("ps aux"))
            print(f"The pod has {len(alert.pod.spec.containers)} containers")

You can access and update in Python any Kubernetes field for Pods, Deployments, and other resources.

A playbook's result is automatically sent to Slack, MSTeams, or other destinations you configure.

.. admonition:: Example Slack Message

    .. image:: /images/crash-report.png


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

   user-guide/builtin-playbooks
   user-guide/alerts
   user-guide/playbook-configuration
   user-guide/slack
   user-guide/prometheus
   user-guide/elasticsearch
   user-guide/architecture

.. toctree::
   :maxdepth: 4
   :caption: Developer Guide
   :hidden:

   developer-guide/writing-playbooks
   developer-guide/general-guidelines
   developer-guide/scheduled-playbooks
   developer-guide/reference
