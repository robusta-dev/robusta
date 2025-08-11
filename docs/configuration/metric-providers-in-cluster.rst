In-cluster Prometheus
=====================

Configure Robusta to use a Prometheus instance running inside your Kubernetes cluster.

Quick Start
-----------

In most cases, Robusta will automatically detect Prometheus in your cluster. No configuration needed!

If auto-detection fails, add the following to your ``generated_values.yaml``:

.. code-block:: yaml

    globalConfig:
        prometheus_url: "http://PROMETHEUS_SERVICE_NAME.NAMESPACE.svc.cluster.local:9090"
        alertmanager_url: "http://ALERTMANAGER_SERVICE_NAME.NAMESPACE.svc.cluster.local:9093"

Then :ref:`update Robusta <Simple Upgrade>`.

Finding Your Service Names
--------------------------

To find your exact Prometheus service name:

.. code-block:: bash

    # List all services in common namespaces
    kubectl get svc -A | grep -E "prometheus|alertmanager"

    # Or check specific namespace
    kubectl get svc -n monitoring
    kubectl get svc -n prometheus

Verification
------------

After configuration, verify the connection:

**Using Robusta UI**:
   
Open the Robusta UI, navigate to any application, and check if CPU/memory graphs are displayed. If graphs appear, the integration is working correctly.

Advanced Configuration
----------------------

Multi-Cluster Prometheus
^^^^^^^^^^^^^^^^^^^^^^^^

If your Prometheus contains data for multiple clusters, tell Robusta how to query data for this cluster only:

.. code-block:: yaml

    globalConfig:
        prometheus_additional_labels:
            cluster: 'CLUSTER_NAME_HERE'

Grafana Alerts
^^^^^^^^^^^^^^

If using Grafana alerts, add these settings:

.. code-block:: yaml

    globalConfig:
        grafana_api_key: <YOUR GRAFANA EDITOR API KEY>
        alertmanager_flavor: grafana

Multi-Tenant Prometheus
^^^^^^^^^^^^^^^^^^^^^^^

For multi-tenant Prometheus or AlertManager, pass the organization ID to all queries:

.. code-block:: yaml

    globalConfig:
        prometheus_additional_headers:
            X-Scope-OrgID: <org id>
        alertmanager_additional_headers:
            X-Scope-OrgID: <org id>

Authentication
^^^^^^^^^^^^^^

If Prometheus and/or AlertManager require authentication, add the following:

.. code-block:: yaml

    globalConfig:
        prometheus_auth: Bearer <YOUR TOKEN> # Replace with your actual token
        alertmanager_auth: Basic <USER:PASSWORD base64-encoded> # Replace with base64-encoded credentials

These settings may be configured independently.

SSL Verification
^^^^^^^^^^^^^^^^

By default, Robusta does not verify the SSL certificate of the Prometheus server.

To enable SSL verification:

.. code-block:: yaml

    runner:
        additional_env_vars:
        - name: PROMETHEUS_SSL_ENABLED
          value: "true"

If you have a custom Certificate Authority (CA) certificate, add one more setting:

.. code-block:: yaml

    runner:
        certificate: "<YOUR BASE-64 ENCODED DATA>" # base64-encoded certificate value

Troubleshooting
---------------

**Connection errors?**
   Test connectivity from Robusta's namespace:
   
   .. code-block:: bash

       # Replace prometheus-service.namespace with your actual service and namespace
       kubectl run test-curl -n robusta --image=curlimages/curl --rm -it -- \
           curl -v http://prometheus-service.namespace.svc.cluster.local:9090/-/healthy