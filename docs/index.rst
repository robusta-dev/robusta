Overview
================================

.. toctree::
   :maxdepth: 4
   :caption: Home
   :hidden:

   home


.. toctree::
   :maxdepth: 4
   :caption: Getting Started
   :hidden:
   
   gettingstarted-index
   Install with Helm <installation>
   Install with ArgoCD <tutorials/argocd-installation>
   tutorials/add-more-clusters
   using-robusta/trackchanges
   using-robusta/enrich-alerts
   Remediate Alerts <using-robusta/remediatealerts>
   Route Alerts <using-robusta/routealerts>
   More tutorials <tutorials/blogs-videos>
   

.. toctree::
   :maxdepth: 4
   :caption: Configuration
   :hidden:

   user-guide/overview
   user-guide/defining-playbook
   user-guide/global-config
   user-guide/sink-configuration
   user-guide/additional-playbooks
   user-guide/Secrets <configuration-secrets>
   user-guide/alert-manager
   user-guide/embeded-prometheus
   upgrade
   uninstall
   tutorials/configuring-automations
   tutorials/prometheus-enrichment
   tutorials/my-first-custom-action


..
   tutorials/alert-correlation

.. toctree::
   :maxdepth: 4
   :caption: Architecture
   :hidden:
    
   Overview <self>
   oss-vs-saas
   Robusta UI Triggers <advanced/robusta-ui-triggers>
   Privacy & Security <advanced/privacy-and-security>



.. toctree::
   :maxdepth: 4
   :caption: Automation
   :hidden:

   catalog/overview
   catalog/triggers/index
   catalog/actions/index
   catalog/sinks/index

.. toctree::
   :maxdepth: 4
   :caption: Extending
   :hidden:

   Write Python Automations <developer-guide/actions/index>
   Modify Robusta Core <developer-guide/platform/index>
   Docs Contributions <developer-guide/platform/docs-contributions>

.. toctree::
   :maxdepth: 4
   :caption: Help
   :hidden:

   help


Robusta has three main parts, all open source:

1. An automations engine for Kubernetes
2. Builtin automations to enrich and fix common alerts
3. Manual troubleshooting tools for everything else

There are additional *optional* components:

4. `An all-in-one bundle with Robusta, the Prometheus Operator, and default Kubernetes alerts <https://home.robusta.dev/prometheus-based-monitoring/?from=docs>`_ [#f1]_
5. `A web UI to see all alerts, changes, and events in your cluster. <http://home.robusta.dev/ui?from=docs>`_ [#f2]_

Standard Architecture
^^^^^^^^^^^^^^^^^^^^^^^

Robusta is installed and managed with Helm.

Automations engine
^^^^^^^^^^^^^^^^^^^^^^
The main component of Robusta is the automation engine, which runs in-cluster as two Kubernetes deployments

robusta-forwarder
    Connects to the APIServer and monitors Kubernetes changes. Forwards them to robusta-runner.

robusta-runner
    Executes playbooks

.. image:: ./images/arch-1/arch-1.png
   :width: 600
   :align: center

Bundled Prometheus stack (optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Robusta includes an optional :ref:`embedded Prometheus stack`, preconfigured with alerts for Kubernetes according to best practices.

If you already use *kube-prometheus-stack*, you can :ref:`point it at Robusta<Sending Alerts to Robusta>` instead.

Web UI (optional)
^^^^^^^^^^^^^^^^^^^^^^
There is a `web UI <http://home.robusta.dev/ui?from=docs>`_ [#f1]_ which provides a single pane of glass to monitor
all your alerts and pods across multiple clusters.

CLI (optional)
^^^^^^^^^^^^^^^^
The :ref:`robusta cli <CLI Commands>` has two main uses:

1. Making it easier to install Robusta by autogenerating Helm values
2. Manually triggering Robusta troubleshooting workflows (e.g. to grab a heap dump from any Java pod)

It also has features useful for developing Robusta itself.

See also
^^^^^^^^^

* `Comparison of Robusta and a bare-bones Prometheus stack without Robusta <https://home.robusta.dev/prometheus-based-monitoring/?from=docs>`_
.. Example Use Cases
.. ~~~~~~~~~~~~~~~~~~

.. .. tab-set::

..     .. tab-item:: Crashing pods

..         .. admonition:: Monitor crashing pods and send their logs to Slack

..             .. image:: /images/crash-report2.png
..                 :width: 700
..                 :align: center

..     .. tab-item:: Event Correlation

..         .. admonition:: Show application updates in Grafana to correlate them with error spikes

..             .. image:: /images/grafana-deployment-enrichment.png
..               :width: 400
..               :align: center

..     .. tab-item:: Remediate alerts

..         .. admonition:: Temporarily increase the HPA maximum so you can go back to sleep

..             .. image:: /images/alert_on_hpa_reached_limit1.png
..                 :width: 600
..                 :align: center

..     .. tab-item:: Debug Pods

..         .. admonition:: Attach the VSCode debugger to a running Python pod without tearing your hair out

..             .. image:: /images/python-debugger.png
..               :width: 600
..               :align: center

..             .. code-block:: bash

..                  robusta playbooks trigger python_debugger name=podname namespace=default

..             See :ref:`Python debugger` for more details


Writing your own automations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Many automations are included, but you can also write your own in Python.

.. details:: View example action (Python)

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

Next Steps
~~~~~~~~~~~~

:ref:`Ready to install Robusta? Get started! <installation>`

`Star us on GitHub to receive updates. <https://github.com/robusta-dev/robusta/>`_

.. rubric:: Footnotes

.. [#f1] These alerts should cause no noise on a healthy cluster. If they're noisy in your env, let us know and we'll fix it.

.. [#f2] This is the only component that isn't open source and it's completely optional. For self-hosting the UI, see :ref:`Self hosting`



