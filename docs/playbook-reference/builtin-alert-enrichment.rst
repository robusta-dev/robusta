.. _builtin-alert-enrichment:

Builtin Alert Enrichment
########################################

Robusta takes Prometheus to the next level by correlating alerts with other observability data.

Testing out Prometheus alerts
*********************************
1. Deploy a broken pod that will be stuck in pending state:

.. code-block:: bash
   :name: cb-apply-pendingpod

   kubectl apply -f https://raw.githubusercontent.com/robusta-dev/kubernetes-demos/main/pending_pods/pending_pod_resources.yaml

2. Trigger a Prometheus alert immediately, skipping the normal delays:

.. code-block:: bash
   :name: cb-trigger-prometheus-alert

   robusta playbooks trigger prometheus_alert alert_name=KubePodCrashLooping namespace=default pod_name=example-pod

.. admonition:: Example Slack Message

    .. image:: /images/simulatedprometheusalert.png
