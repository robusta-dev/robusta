Architecture
==================

Robusta runs in-cluster as two Kubernetes deployments

* robusta-forwarder - Connects to the APIServer and monitors Kubernetes changes. Forwards them to robusta-runner.
* robusta-runner - Receives all events, evaluates playbooks, sends notifications

.. image:: ../images/arch-1/arch-1.png
   :width: 600
   :align: center

Robusta has some optional components, described below.

Bundled Prometheus (Optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Install Robusta with :ref:`Prometheus included <embedded Prometheus stack>`. This is powered by ``kube-prometheus-stack``.

Alternatively, you can :ref:`integrate an existing Prometheus with Robusta <Sending Alerts to Robusta>`.

Web UI (Optional)
^^^^^^^^^^^^^^^^^^^^^^

The Robusta `SaaS platform <http://home.robusta.dev/ui?from=docs>`_ provides a single pane of glass for all your alerts and clusters.

CLI (Optional)
^^^^^^^^^^^^^^^^
The ``robusta`` cli makes it easier to install Robusta by auto-generating Helm values.

Next Steps
^^^^^^^^^^^^^

:ref:`Ready to install Robusta? Get started. <install>`
