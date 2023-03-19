:hide-toc:

Quick Install
===============

.. toctree::
   :maxdepth: 1
   :hidden:

   all-in-one-installation
   extend-prometheus-installation
   standalone-installation

Robusta can be installed three ways:

* :ref:`All in one package <Monitor Kubernetes from Scratch>` *(recommended, includes robusta + prometheus)*
* :ref:`Integrate existing Prometheus <Integrate with Existing Prometheus>`
* :ref:`Standalone (no Prometheus at all) <Barebones Installation>`

What about Thanos/Cortex/Mimir/VictoriaMetrics?
********************************************************
Any Prometheus-compatible solution is fine. Just follow instructions under :ref:`Integrate with Existing Prometheus`

Can I use Robusta with DataDog?
********************************************************
We have a DataDog integration available. Try it out.

Is NewRelic supported?
**********************************
It's being planned, speak to us on Slack.

Does Robusta replace monitoring tools?
*************************************************************
Robusta's :ref:`all-in-one package <Monitor Kubernetes from Scratch>` is a complete monitoring and observability solution.

Alternatively, you can keep your existing tools and add-on robusta.
