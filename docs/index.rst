Welcome to Robusta
================================

Robusta is an open source platform for Kubernetes troubleshooting and automation.

Just like Docker is infrastructure-as-code for *deploying* applications, Robusta is infrastructure-as-code for
*maintaining* Kubernetes applications and handling their alerts.

Robusta works with your existing applications and automates their day2 operations.

Handling alerts with Robusta
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We're building a massive open source database of errors and Prometheus alerts.

Robusta receives alerts by webhook from Prometheus, AlertManager, and other solutions. It then:

1. Gathers extra context
2. Identifies possible root causes
3. Suggests fixes
4. Automates applying workarounds

Manual troubleshooting
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Not every problem can be diagnosed automatically, so Robusta lets you:

1. Attach debuggers to running pods
2. Perform CPU profiling on K8s apps
3. Get memory dumps from K8s apps

Change and error tracking
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Robusta listens to API Server events. Using this it:

1. Adds extra context to Grafana (like showing when applications updated)
2. Notifies you on errors like crashing pods

Other Day2 operations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can also use Robusta's automation framework to:

1. Easily write chaos-engineering scenarios in Python.
2. Automate the response to any Prometheus alert or Kubernetes event

Examples
~~~~~~~~~~~~~~~~~~~~

.. tab-set::

    .. tab-item:: Crashing pods

        .. admonition:: When a pod crashes, fetch the logs and send a message to Slack.

            .. image:: /images/crash-report2.png
                :width: 700
                :align: center

            .. code-block:: yaml

                # this is configured by default using something like this:
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

:ref:`Want to learn more? Learn how it works <How it works>`

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

   getting-started/how-it-works
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
