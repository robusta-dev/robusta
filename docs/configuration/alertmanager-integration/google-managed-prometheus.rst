Google Managed Prometheus Alerts
=================================

.. warning::

   Due to updates in the Google Managed Prometheus API, these instructions may be outdated.
   Please contact our team for support on Slack (https://bit.ly/robusta-slack) or by email (support@robusta.dev).
   We're working on updating the documentation.

This guide shows how to send alerts from `Google Managed Prometheus <https://cloud.google.com/stackdriver/docs/managed-prometheus>`_ to Robusta.

.. note::

   **Using Google Managed Alertmanager?** For Google Managed Prometheus (GMP) managed Alertmanager, see the dedicated guide: :doc:`google-managed-alertmanager`

For configuring metric querying from Google Managed Prometheus, see :doc:`/configuration/metric-providers-google`.

Prerequisites
****************
An instance of Google Managed Prometheus with the following components configured:

* Prometheus Frontend (`Frontend Instructions <https://cloud.google.com/stackdriver/docs/managed-prometheus/query#ui-prometheus>`_)
* Node Exporter (`Node Exporter Instructions <https://cloud.google.com/stackdriver/docs/managed-prometheus/exporters/node_exporter>`_)
* Scraping configuration for Kubelet and cAdvisor (`Kubelet/cAdvisor Instructions <https://cloud.google.com/stackdriver/docs/managed-prometheus/exporters/kubelet-cadvisor>`_)
* Kube State Metrics (`Kube State Metrics Instructions <https://cloud.google.com/stackdriver/docs/managed-prometheus/exporters/kube_state_metrics>`_)

Send Alerts to Robusta
********************************************

To send alerts to Robusta, create an AlertManager configuration file with the name ``alertmanager.yaml``:

.. code-block:: yaml

   receivers:
     - name: 'robusta'
       webhook_configs:
         - url: 'http://<helm-release-name>-runner.<namespace>.svc.cluster.local/api/alerts'
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

To enable Robusta to pull metrics from Google Managed Prometheus, see :doc:`/configuration/metric-providers-google`.
