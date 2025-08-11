External Prometheus
===================

Configure Robusta to use a Prometheus instance running outside your Kubernetes cluster, including centralized solutions like Thanos or Mimir.

Quick Start
-----------

Add the following to your ``generated_values.yaml``:

.. code-block:: yaml

    globalConfig:
        prometheus_url: "https://prometheus.example.com:9090"
        alertmanager_url: "https://alertmanager.example.com:9093"

Then :ref:`update Robusta <Simple Upgrade>`.

Configuration Examples
----------------------

**Basic External Prometheus**:

.. code-block:: yaml

    globalConfig:
        prometheus_url: "https://prometheus.company.com:9090"
        alertmanager_url: "https://alertmanager.company.com:9093"

**Thanos Query**:

.. code-block:: yaml

    globalConfig:
        prometheus_url: "https://thanos-query.monitoring.company.com:9090"
        alertmanager_url: "https://alertmanager.monitoring.company.com:9093"

**Cortex/Mimir**:

.. code-block:: yaml

    globalConfig:
        prometheus_url: "https://mimir.company.com/prometheus"
        alertmanager_url: "https://mimir.company.com/alertmanager"

Authentication
--------------

**Bearer Token**:

.. code-block:: yaml

    globalConfig:
        prometheus_url: "https://prometheus.example.com:9090"
        prometheus_auth: "Bearer YOUR_TOKEN_HERE"
        alertmanager_auth: "Bearer YOUR_TOKEN_HERE"

**Basic Authentication**:

.. code-block:: yaml

    globalConfig:
        prometheus_url: "https://prometheus.example.com:9090"
        # Base64 encode: echo -n "username:password" | base64
        prometheus_auth: "Basic dXNlcm5hbWU6cGFzc3dvcmQ="
        alertmanager_auth: "Basic dXNlcm5hbWU6cGFzc3dvcmQ="

Multi-cluster Setup
-------------------

When using a centralized Prometheus for multiple clusters:

**Option 1: Filter with labels**

.. code-block:: yaml

    globalConfig:
        prometheus_url: "https://central-prometheus.company.com:9090"
        
        # Add cluster label to all queries
        prometheus_additional_labels:
            cluster: 'production-us-east'

**Option 2: Filter with query string**

.. code-block:: yaml

    globalConfig:
        prometheus_url: "https://central-prometheus.company.com:9090"
        
        # Append query parameters to all requests
        prometheus_url_query_string: "cluster=production-us-east&region=us-east-1"

.. note::

    When using external Prometheus with multiple clusters, ensure all alerts contain a label named ``cluster_name`` or ``cluster``, matching the :ref:`cluster_name defined in Robusta's configuration <Global Config>`. This is necessary to identify which robusta-runner should receive alerts.

SSL/TLS Configuration
---------------------

**Enable SSL verification** (recommended for production):

.. code-block:: yaml

    globalConfig:
        prometheus_url: "https://prometheus.example.com:9090"
    
    runner:
        additional_env_vars:
        - name: PROMETHEUS_SSL_ENABLED
          value: "true"

**Custom CA Certificate**:

.. code-block:: yaml

    globalConfig:
        prometheus_url: "https://prometheus.internal.company.com:9090"
    
    runner:
        additional_env_vars:
        - name: PROMETHEUS_SSL_ENABLED
          value: "true"
        
        # Base64 encode your CA certificate
        certificate: |
            LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSURFVENDQWZtZ0F3SUJBZ0lVT...

Network Connectivity
--------------------

Ensure Robusta can reach your external Prometheus:

1. **Allow egress traffic** from Robusta's namespace to your Prometheus URL
2. **Configure firewall rules** if Prometheus is behind a corporate firewall
3. **Set up VPN or private endpoints** if needed

Test connectivity:

.. code-block:: bash

    # From within the cluster
    kubectl run test-curl --image=curlimages/curl --rm -it -- \
        curl -v https://prometheus.example.com:9090/-/healthy

Advanced Configuration
----------------------

**Custom Headers**:

.. code-block:: yaml

    globalConfig:
        prometheus_additional_headers:
            X-Custom-Header: "custom-value"
            X-Scope-OrgID: "tenant-123"

**Separate Prometheus Instances per Cluster**:

If you prefer separate Prometheus URLs per cluster instead of filtering:

.. code-block:: yaml

    # In production cluster's values
    globalConfig:
        prometheus_url: "https://prometheus-prod.company.com:9090"
    
    # In staging cluster's values
    globalConfig:
        prometheus_url: "https://prometheus-staging.company.com:9090"

Troubleshooting
---------------

**Connection timeouts?**
   - Check network connectivity and firewall rules
   - Verify the URL is accessible from within your cluster
   - Ensure any VPN or private endpoint is configured

**Authentication errors?**
   - Double-check your token or credentials
   - Ensure proper Base64 encoding for Basic auth
   - Verify the authentication header format

**SSL/TLS errors?**
   - Enable SSL verification if using HTTPS
   - Add custom CA certificate if using internal certificates
   - Check certificate validity and hostname matching

**No metrics showing?**
   - Verify Prometheus has metrics for your cluster
   - Check cluster filtering configuration
   - Ensure time sync between cluster and Prometheus

Next Steps
----------

- Configure :doc:`alert routing </notification-routing/index>`
- Set up :doc:`AI-powered insights </configuration/holmesgpt/index>`
- Learn about :doc:`common configuration options <metric-providers>`