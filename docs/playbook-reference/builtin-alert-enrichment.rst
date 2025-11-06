.. _builtin-alert-enrichment:

Alert Enrichment
########################################

Ever feel overwhelmed by alerts that lack context? Robusta enriches alerts automatically and lets you create custom enrichment rules.

.. note::

   **Looking for automatic AI enrichment?** Check out :doc:`HolmesGPT </configuration/holmesgpt/main-features>` for zero-configuration AI-powered alert enrichment that automatically investigates alerts and provides root cause analysis.

Builtin Alert Enrichment
*********************************

Robusta automatically enriches Prometheus alerts with relevant Kubernetes context:

* **Pod events** - Recent events related to the affected pod
* **Pod logs** - Relevant log excerpts from crashing or failing containers
* **Resource metrics** - CPU, memory, and other resource usage data
* **Related Kubernetes objects** - Deployments, ReplicaSets, ConfigMaps, etc.

This happens automatically for common Prometheus alerts without any configuration. To extend it to your own Prometheus alerts you can define custom playbooks.

Testing Alert Enrichment
^^^^^^^^^^^^^^^^^^^^^^^^^^

1. Deploy a broken pod:

.. code-block:: bash
   :name: cb-apply-pendingpod

   kubectl apply -f https://raw.githubusercontent.com/robusta-dev/kubernetes-demos/main/pending_pods/pending_pod_resources.yaml

2. Trigger a Prometheus alert immediately:

.. code-block:: bash
   :name: cb-trigger-prometheus-alert

   robusta playbooks trigger prometheus_alert alert_name=KubePodCrashLooping namespace=default pod_name=example-pod

.. admonition:: Example Enriched Alert

    .. image:: /images/simulatedprometheusalert.png

Custom Alert Enrichment
*********************************

Create custom enrichment rules to:

* Reduce MTTR by automatically gathering system state and logs when alerts fire
* Make faster decisions on which team needs to investigate
* Link alerts to runbooks and documentation for better knowledge sharing

Get started with these examples:

.. toctree::
   :maxdepth: 1

   prometheus-examples/bash-alert-enrichment
   prometheus-examples/link-alert-enrichment
