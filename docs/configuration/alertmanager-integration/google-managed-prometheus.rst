Google Managed Prometheus
==========================

This guide walks you through integrating your `Google Managed Prometheus <https://cloud.google.com/stackdriver/docs/managed-prometheus>`_ with Robusta.

You will need to configure a push integration.


Setting Up Google Managed Prometheus
-------------------------------------

1. **Install Prometheus Frontend**

   Follow the `setup instructions <https://cloud.google.com/stackdriver/docs/managed-prometheus/setup-managed>`_ to install the Prometheus frontend.

2. **Configure Prometheus in Robusta**

   Add to your ``generated_values.yaml``:

.. code-block:: yaml

    prometheus_url: "http://frontend.default.svc.cluster.local:9090"
    alertmanager_url: "http://alertmanager.gmp-system.svc.cluster.local:9093"

3. **Install Node Exporter**

   Run through the `Node Exporter <https://cloud.google.com/stackdriver/docs/managed-prometheus/exporters/node_exporter>`_ instructions to setup Node Exporter.

4. **Update Kubelet Scraping Config**

   Run ``kubectl -n gmp-public edit operatorconfig config`` and add the following config to change the Kubelet scraping interval. Detailed instructions are available at `Kubelet and cAdvisor <https://cloud.google.com/stackdriver/docs/managed-prometheus/exporters/kubelet-cadvisor>`_.


.. code-block:: yaml

    collection:
    kubeletScraping:
        interval: 30s


5. **Install Kube-State-Metrics**

   Apply **Install Kube State Metrics** and **Define rules and alerts** configs in the `Kube State Metrics <https://cloud.google.com/stackdriver/docs/managed-prometheus/exporters/kube_state_metrics>`_ guide.


Configure Push Integration
----------------------------

A push integration sends alerts to Robusta. To configure it, edit AlertManager's configuration:

To ensure that Alertmanager applies the new configuration, create a Kubernetes secret named `alertmanager`. This can be achieved using the following kubectl command:

.. code-block:: bash

   kubectl create secret generic alertmanager \
     -n gmp-public \
     --from-file=alertmanager.yaml

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


This creates a secret in the `gmp-public` namespace with the contents of your `alertmanager.yaml` file.

The Alertmanager deployment will use this secret to configure its alert forwarding settings.
