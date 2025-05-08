Architecture
==================

The base installation for Robusta runs in-cluster as two Kubernetes deployments

* robusta-forwarder - Connects to the APIServer and monitors Kubernetes changes. Forwards them to robusta-runner.
* robusta-runner - Receives all events, evaluates playbooks, sends notifications

.. image:: ../images/arch-1/arch-1.png
   :width: 600
   :align: center

Optionally, Robusta has some additional components, described below.

HolmesGPT (Optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Robusta's next generation AI-engine that investigates alerts automatically. See :ref:`AI Analysis <AI Analysis>`.

Bundled Prometheus (Optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Install Robusta with :ref:`Prometheus included <embedded Prometheus stack>`. This is powered by ``kube-prometheus-stack``.

Alternatively, you can :ref:`integrate an existing Prometheus with Robusta <Integrating with Prometheus>`.

Web UI (Optional)
^^^^^^^^^^^^^^^^^^^^^^

The Robusta `SaaS platform <http://home.robusta.dev/?from=docs>`_ provides a single pane of glass for all your alerts and clusters.

On commercial plans, the UI is available for self-hosting in your own environment.

CLI (Optional)
^^^^^^^^^^^^^^^^
The ``robusta`` cli makes it easier to install Robusta by auto-generating Helm values.

Next Steps
^^^^^^^^^^^^^

:ref:`Ready to install Robusta? Get started. <install>`
