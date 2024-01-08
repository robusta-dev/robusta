Google Managed Prometheus
==========================

This guide walks you through integrating your `Google Managed Prometheus <https://cloud.google.com/stackdriver/docs/managed-prometheus>`_ with Robusta.

You will need to configure two integrations: one to send alerts to Robusta and another to let Robusta query metrics and create silences.

Prerequisites
****************
An instance of Google Managed Prometheus with the following components configured:

* Prometheus Frontend (`Instructions <https://cloud.google.com/stackdriver/docs/managed-prometheus/query#ui-prometheus>`_)
* Node Exporter (`Instructions <https://cloud.google.com/stackdriver/docs/managed-prometheus/exporters/node_exporter>`_)
* Scraping configuration for Kubelet and cAdvisor (`Instructions <https://cloud.google.com/stackdriver/docs/managed-prometheus/exporters/kubelet-cadvisor>`_)
* Kube State Metrics (`Instructions <https://cloud.google.com/stackdriver/docs/managed-prometheus/exporters/kube_state_metrics>`_)

Send Alerts to Robusta
********************************************

To send alerts to Robusta, create an AlertManager configuration file with the name ``alertmanager.yaml``:

.. code-block:: yaml

   receivers:
     - name: 'robusta'
       webhook_configs:
         - url: 'http://robusta-runner.default.svc.cluster.local/api/alerts'
           send_resolved: true
     - name: 'default-receiver'

   route:
     routes:
       - receiver: 'robusta'
         group_by: [ '...' ]
         group_wait: 1s
         group_interval: 1s
         matchers:
           - severity =~ ".*"
         repeat_interval: 4h
         continue: true
     receiver: 'default-receiver'

Apply this file as a secret to your cluster using the following command:

.. code-block:: bash

   kubectl create secret generic alertmanager \
     -n gmp-public \
     --from-file=alertmanager.yaml

Verify it Works
------------------------------

Run this command to send a dummy alert to the GMP AlertManager in your cluster:

.. code-block:: yaml

   robusta demo-alert --alertmanager-url='http://alertmanager.gmp-system.svc.cluster.local:9093

You know it works if you receive an alert from Robusta.

Configure Metric Querying
******************************

A pull integration lets Robusta pull metrics and create silences.

Add the following to Robusta's configuration(``generated_values.yaml``) and :ref:`update Robusta <Simple Upgrade>`.

.. code-block:: yaml

   globalConfig: # this line should already exist
      prometheus_url: "http://frontend.default.svc.cluster.local:9090"
      alertmanager_url: "http://alertmanager.gmp-system.svc.cluster.local:9093"


Verify it Works
---------------------
Run the following command to create a Pod that triggers an OOMKilled alert

.. code-block:: yaml

   kubectl apply -f https://raw.githubusercontent.com/robusta-dev/kubernetes-demos/main/oomkill/oomkill_job.yaml

You know it works if you receive an alert from Robusta with a graph.
