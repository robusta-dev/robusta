Welcome to Robusta
================================

Robusta is the Swiss Army Knife of Kubernetes troubleshooting and automation. You can use Robusta to:

1. Manually troubleshoot errors, debug pods, run cpu profilers, etc
2. Add missing context to alerts
3. Remediate alerts by clicking a single button in Slack
4. Complement Prometheus with monitoring of *discrete* events like crashing pods

We recommend you start with `Robusta.dev <https://home.robusta.dev/>`_, do a :ref:`60-second install <Installation Guide>`,
and then read the docs for advanced features.

Examples
~~~~~~~~~~~~~~~~~~

Most of these can be installed pre-configured, but we show the configuration anyway to illustrate concepts.

.. tab-set::

    .. tab-item:: Crashing pods

        .. admonition:: When a pod crashes, fetch the logs and send a message to Slack.

            .. image:: /images/crash-report2.png
                :width: 700
                :align: center

            .. code-block:: yaml

                triggers:
                  - on_prometheus_alert:
                      alert_name: KubePodCrashLooping
                actions:
                  - logs_enricher: {}
                sinks:
                  - slack

            See :ref:`Restart loop reporter` for more details

    .. tab-item:: Change tracking

        .. admonition:: Show application updates in Grafana

            .. image:: /images/grafana-deployment-enrichment.png
              :width: 400
              :align: center

            .. code-block:: yaml

                triggers:
                  - on_deployment_update: {}
                actions:
                  - add_deployment_lines_to_grafana:
                      grafana_url: <grafana_url>
                      grafana_api_key: <grafana_api_key>
                      grafana_dashboard_uid: <which_grafana_dashboard_to_update>

            See :ref:`Add deployment lines to grafana` for more details

    .. tab-item:: Chatops

        .. admonition:: Increase the number of replicas from Slack.

            .. image:: /images/alert_on_hpa_reached_limit1.png
                :width: 600
                :align: center

            .. code-block:: yaml

                triggers:
                - on_horizontalpodautoscaler_update: {}
                actions:
                - alert_on_hpa_reached_limit: {}


    .. tab-item:: Debug pods with VSCode

        .. admonition:: Attach a Python debugger to a running pod:

            .. image:: /images/python-debugger.png
              :width: 600
              :align: center


            .. code-block:: bash

                 robusta playbooks trigger python_debugger name=podname namespace=default

            See :ref:`Python debugger` for more details

How it works
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Robusta automates everything that happens **after** you deploy your application.

It is somewhat like Zapier/IFTTT for devops, with an emphasis on 50+ prebuilt automations and not just "build your own".

You configure automations in a three-part yaml:

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

Automations run via webhook so if they fail it wont bring down your environment.

Robusta is configured in YAML and extended in Python.

What's in the Box
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
                MarkdownBlock("*Oh no!* An alert occurred on " + pod_name)
                FileBlock("crashing-pod.log", pod_logs)
            ])



FAQ
~~~~~~~~~~~~~~~~~~~~

How is this different from webhooks
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This is powered by webhooks! The advantage is configuring prebuilt webhooks using YAML instead of writing
them from scratch as code.

We also let you re-use the same webhook action with multiple triggers: e.g. AlertManager, the APIServer, and more.

Lastly, if you do want to write a webhook action from scratch, we make it easier with our Python API.

Architecture
~~~~~~~~~~~~~~~~~~~~
Robusta can be used as

.. dropdown:: A complete Kubernetes monitoring stack
    :color: light

    Robusta will install a bundled Prometheus stack. Includes:

    * Robusta automations engine + builtin automations
    * Prometheus Operator, AlertManager, and Grafana
    * Out of the box alerts fine-tuned for Kubernetes

.. dropdown:: An automations engine for your existing stack
    :color: light

    Robusta will integrate with external tools like your existing Prometheus, Datadog, or Elasticsearch. Includes:

    * Robusta automations engine + builtin automations

Next Steps
~~~~~~~~~~~~

:ref:`Ready to install Robusta? Get started! <Installation Guide>`

Want a better frontend for AlertManager? Try `the Robusta UI <https://home.robusta.dev/ui/>`_. It shows alerts, changes
to your cluster, and data from Robusta. See everything on a single timeline and slice/dice by cluster, microservice,
and alert type.

`Star us on Github to receive updates. <https://github.com/robusta-dev/robusta/>`_

.. toctree::
   :hidden:

   self

.. toctree::
   :maxdepth: 4
   :caption: Getting Started
   :hidden:

   getting-started/installation
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

   user-guide/example-playbook
   user-guide/configuration
   user-guide/upgrade
   user-guide/robusta-cli
   user-guide/architecture

.. toctree::
   :maxdepth: 4
   :caption: Developer Guide
   :hidden:

   developer-guide/actions/index
   developer-guide/platform/index
