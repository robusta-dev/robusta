VictoriaMetrics
===============

Configure Robusta to use VictoriaMetrics as your metrics provider.

Quick Start
-----------

VictoriaMetrics is often auto-detected by Robusta. If not, add the following to your ``generated_values.yaml``:

.. code-block:: yaml

    globalConfig:
        prometheus_url: "http://vmsingle-victoria-metrics.default.svc.cluster.local:8429"
        alertmanager_url: "http://vmalertmanager-victoria-metrics.default.svc.cluster.local:9093"

Then :ref:`update Robusta <Simple Upgrade>`.

Common Configurations
---------------------

**VMSingle (Single-node VictoriaMetrics)**:

.. code-block:: yaml

    globalConfig:
        prometheus_url: "http://vmsingle-victoria-metrics.default.svc.cluster.local:8429"
        alertmanager_url: "http://vmalertmanager-victoria-metrics.default.svc.cluster.local:9093"

**VMCluster (Clustered VictoriaMetrics)**:

.. code-block:: yaml

    globalConfig:
        prometheus_url: "http://vmselect-victoria-metrics.default.svc.cluster.local:8481/select/0/prometheus"
        alertmanager_url: "http://vmalertmanager-victoria-metrics.default.svc.cluster.local:9093"

**With VMAuth (Authentication proxy)**:

.. code-block:: yaml

    globalConfig:
        prometheus_url: "http://vmauth-victoria-metrics.default.svc.cluster.local:8427"
        prometheus_auth: "Bearer YOUR_TOKEN"

Finding Your Service Names
--------------------------

List VictoriaMetrics services in your cluster:

.. code-block:: bash

    # Find VictoriaMetrics services
    kubectl get svc -A | grep -E "vmsingle|vmselect|vmalert"
    
    # Check specific namespace
    kubectl get svc -n victoria-metrics-system

Multi-cluster Setup
-------------------

For VictoriaMetrics monitoring multiple clusters:

.. code-block:: yaml

    globalConfig:
        prometheus_url: "http://vmsingle-victoria-metrics.default.svc.cluster.local:8429"
        
        # Add cluster label to all queries
        prometheus_additional_labels:
            cluster: 'production-cluster'

Advanced Features
-----------------

**Query Parameters**:

VictoriaMetrics supports additional query parameters for optimization:

.. code-block:: yaml

    globalConfig:
        prometheus_url: "http://vmsingle-victoria-metrics.default.svc.cluster.local:8429"
        
        # Add VictoriaMetrics-specific parameters
        prometheus_url_query_string: "nocache=1&max_lookback=1h"

**Multi-tenant Setup**:

For multi-tenant VictoriaMetrics:

.. code-block:: yaml

    globalConfig:
        prometheus_additional_headers:
            X-Scope-OrgID: "tenant-123"

Compatibility Notes
-------------------

- VictoriaMetrics is fully compatible with Prometheus API
- Supports all Prometheus query features used by Robusta
- The flags API is supported (no need to disable ``check_prometheus_flags``)
- Works with both VMAlert and standard AlertManager

Verification
------------

After configuration:

1. **Check connectivity**:

   .. code-block:: bash

       kubectl run test-curl --image=curlimages/curl --rm -it -- \
           curl -v http://vmsingle-victoria-metrics.default.svc.cluster.local:8429/api/v1/query?query=up

2. **Verify in Robusta UI**: Check if metrics graphs appear for your applications

3. **Test with a demo alert**:

   .. code-block:: bash

       kubectl apply -f https://raw.githubusercontent.com/robusta-dev/kubernetes-demos/main/oomkill/oomkill_job.yaml

Troubleshooting
---------------

**Auto-detection not working?**
   - Ensure VictoriaMetrics service name contains "victoria" or "vmsingle"
   - Check that services are in standard namespaces
   - Manually configure if using non-standard names

**Connection errors?**
   - For VMCluster, ensure you're using vmselect endpoint, not vmstorage
   - Check the correct port (8429 for vmsingle, 8481 for vmselect)
   - Verify no network policies blocking access

**Metrics not showing?**
   - Ensure VictoriaMetrics is scraping your cluster metrics
   - Check retention settings if historical data is missing
   - Verify time sync between cluster and VictoriaMetrics

Performance Tips
----------------

- VictoriaMetrics is highly efficient with resources
- Consider enabling query caching for better performance
- Use downsampling for long-term retention
- Configure appropriate retention periods

Next Steps
----------

- Configure :doc:`alert routing </notification-routing/index>`
- Set up :doc:`VictoriaMetrics alerts </configuration/alertmanager-integration/victoria-metrics>`
- Learn about :doc:`common configuration options <metric-providers>`