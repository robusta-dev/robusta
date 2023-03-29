Architecture
==================

The main component of Robusta is the automation engine, which runs in-cluster as two Kubernetes deployments

* robusta-forwarder - Connects to the APIServer and monitors Kubernetes changes. Forwards them to robusta-runner.
* robusta-runner - Receives all events, runs Robusta rules, send notifications

.. image:: ../images/arch-1/arch-1.png
   :width: 600
   :align: center

Additionally, Robusta has some optional components, described below.

Bundled Prometheus stack (optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Robusta includes an optional :ref:`embedded Prometheus stack`, including default alerts for Kubernetes.

If you already use *kube-prometheus-stack*, you can :ref:`point it at Robusta <Sending Alerts to Robusta>` instead of installing the bundled Prometheus.

Web UI (optional)
^^^^^^^^^^^^^^^^^^^^^^
There is a `web UI <http://home.robusta.dev/ui?from=docs>`_ which provides a single pane of glass to monitor
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


Next Steps
~~~~~~~~~~~~

:ref:`Ready to install Robusta? Get started! <installation>`

`Star us on GitHub to receive updates. <https://github.com/robusta-dev/robusta/>`_
