Welcome to Robusta!
=====================
Robusta is an open source platform for automated troubleshooting and maintenance. It turns Kubernetes expertise into
reusable code.

Robusta automates everything that happens **after** you deploy your application. It contains:

1. A library of high-level actions you can use instead of writing your own webhooks or scripts.
2. A Python library to write your own actions
3. Preconfigured actions for common errors and Prometheus alerts

Examples
~~~~~~~~~~~~~~~~~~


.. tab-set::

    .. tab-item:: Crashing pods

        .. image:: /images/crash-report2.png
            :width: 700
            :align: center

        When a pod crashes, fetch the logs and send a message to Slack.

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

        .. image:: /images/grafana-deployment-enrichment.png
          :width: 400
          :align: center

        Write annotations to Grafana showing when applications are updated.

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

        .. image:: /images/alert_on_hpa_reached_limit1.png
            :width: 600
            :align: center

        Increase the number of replicas from Slack.

        .. code-block:: yaml

            triggers:
            - on_horizontalpodautoscaler_update: {}
            actions:
            - alert_on_hpa_reached_limit: {}


    .. tab-item:: Debug pods with VSCode

        .. image:: /images/python-debugger.png
          :width: 600
          :align: center

        Attach a Python debugger to a running pod:

        .. code-block:: bash

             robusta playbooks trigger python_debugger name=myapp namespace=default

        See :ref:`Python debugger` for more details

How it works
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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

Why Robusta
~~~~~~~~~~~

Knowledge sharing is hard.

Docker and Terraform democratize the ability to setup environments. They make the instructions for installing servers
reusable and reproducible. They did so by turning knowledge to code.

Robusta does the same for error handling. Our vision is a world where every company, no matter how big or small,
can benefit from the knowledge of the world's best experts. We strive to encapsulate their knowledge in reusable and
reproducible code.

Knowledge is captured as actions. :ref:`Robusta has over 50 builtin actions <Actions>`. You can easily write your own
in Python:

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

Want a better UI for Kubernetes? Try `the Robusta UI <https://home.robusta.dev/ui/>`_. It shows all the data that
Robusta automations gather and more.

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

   user-guide/playbook-repositories
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
