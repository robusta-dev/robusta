Google Managed Prometheus
=========================

.. warning::

   Due to updates in the Google Managed Prometheus API, these instructions may be outdated.
   Please contact our team for support on Slack (https://bit.ly/robusta-slack) or by email (support@robusta.dev).
   We're working on updating the documentation.

Configure Robusta to use Google Cloud's Managed Service for Prometheus.

Prerequisites
-------------

Before configuring Robusta, ensure you have:

1. Google Managed Prometheus configured with:
   
   - `Prometheus Frontend <https://cloud.google.com/stackdriver/docs/managed-prometheus/query#ui-prometheus>`_
   - `Node Exporter <https://cloud.google.com/stackdriver/docs/managed-prometheus/exporters/node_exporter>`_
   - `Kubelet/cAdvisor scraping <https://cloud.google.com/stackdriver/docs/managed-prometheus/exporters/kubelet-cadvisor>`_
   - `Kube State Metrics <https://cloud.google.com/stackdriver/docs/managed-prometheus/exporters/kube_state_metrics>`_

Quick Start
-----------

Add the following to your ``generated_values.yaml``:

.. code-block:: yaml

    globalConfig:
        prometheus_url: "http://frontend.default.svc.cluster.local:9090"
        alertmanager_url: "http://alertmanager.gmp-system.svc.cluster.local:9093"
        check_prometheus_flags: false  # Required for Google Managed Prometheus

Then :ref:`update Robusta <Simple Upgrade>`.

Service Locations
-----------------

Google Managed Prometheus typically deploys services in these locations:

**Prometheus Frontend**:
   - Namespace: ``default`` (or where you deployed it)
   - Service: ``frontend``
   - Port: ``9090``

**AlertManager**:
   - Namespace: ``gmp-system``
   - Service: ``alertmanager``
   - Port: ``9093``

Verify your exact service names:

.. code-block:: bash

    # Check frontend service
    kubectl get svc -n default | grep frontend
    
    # Check AlertManager service
    kubectl get svc -n gmp-system | grep alertmanager

Configuration Notes
-------------------

.. warning::

   Google Managed Prometheus does not support the Prometheus flags API. Always set ``check_prometheus_flags: false``.

- The Prometheus Frontend must be deployed separately (it's not included by default)
- Ensure all required exporters are configured for full functionality
- Google Managed Prometheus uses a different architecture than standard Prometheus

Verification
------------

After configuration, verify the integration:

1. **Check connectivity**:

   .. code-block:: bash

       kubectl run test-curl --image=curlimages/curl --rm -it -- \
           curl -v http://frontend.default.svc.cluster.local:9090/-/healthy

2. **Test with a demo alert**:

   .. code-block:: bash

       kubectl apply -f https://raw.githubusercontent.com/robusta-dev/kubernetes-demos/main/oomkill/oomkill_job.yaml

   You should receive an alert with metrics attached.

3. **Check Robusta logs**:

   .. code-block:: bash

       kubectl logs -n robusta deployment/robusta-runner | grep -i prometheus


Next Steps
----------

- Configure :doc:`alert routing </notification-routing/index>`
- Set up :doc:`Google Cloud alerting integration </configuration/alertmanager-integration/google-managed-prometheus>`
- Learn about :doc:`common configuration options <metric-providers>`