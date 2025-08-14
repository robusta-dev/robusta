Coralogix
=========

Configure Robusta to use Coralogix's managed Prometheus service.

Prerequisites
-------------

1. A Coralogix account with Prometheus enabled
2. Your Logs Query API key from Coralogix

Quick Start
-----------

1. **Get your PromQL endpoint**:
   
   Check the `Coralogix endpoints documentation <https://coralogix.com/docs/integrations/coralogix-endpoints/#promql>`_ for your region's endpoint.

2. **Get your API key**:
   
   - Log into Coralogix
   - Go to **Data Flow → API Keys**
   - Copy the **Logs Query Key** (or generate one if needed)

3. **Create a Kubernetes secret**:

   .. code-block:: bash

       kubectl create secret generic coralogix-secret -n robusta \
           --from-literal=logs_query_key=YOUR_LOGS_QUERY_KEY

4. **Configure Robusta** - add to ``generated_values.yaml``:

   .. code-block:: yaml

       globalConfig:
           prometheus_url: "https://prom-api.coralogix.com"  # Use your region's endpoint
           check_prometheus_flags: false  # Required for Coralogix
           
           # If monitoring multiple clusters, add cluster filtering:
           # prometheus_additional_labels:
           #   cluster: 'production-cluster'
           
       runner:
           additional_env_vars:
           - name: PROMETHEUS_SSL_ENABLED
             value: "true"
           - name: CORALOGIX_PROMETHEUS_TOKEN
             valueFrom:
               secretKeyRef:
                 name: coralogix-secret
                 key: logs_query_key

5. :ref:`Update Robusta <Simple Upgrade>`

Regional Endpoints
------------------

Use the correct endpoint for your Coralogix region:

- **US1**: ``https://prom-api.coralogix.com``
- **EU1**: ``https://prom-api.eu2.coralogix.com``
- **AP1**: ``https://prom-api.app.coralogix.in``
- **EU2**: ``https://prom-api.eu2.coralogix.com``

Check the `official documentation <https://coralogix.com/docs/integrations/coralogix-endpoints/#promql>`_ for the most up-to-date list.

Multi-cluster Setup
-------------------

When using Coralogix for multiple clusters, add cluster labels to differentiate metrics:

.. code-block:: yaml

    globalConfig:
        prometheus_url: "https://prom-api.coralogix.com"
        check_prometheus_flags: false
        
        # Add cluster label to all queries
        prometheus_additional_labels:
            cluster: 'production-us-east'
            environment: 'production'

Important Notes
---------------

.. warning::

   Coralogix does not support the Prometheus flags API. Always set ``check_prometheus_flags: false``.

- Use the Logs Query Key, not other API key types
- SSL is required and automatically enabled
- Ensure your API key has permissions to query metrics


Next Steps
----------

- Configure :doc:`alert routing </notification-routing/index>`
- Set up :doc:`Coralogix alerts integration </configuration/alertmanager-integration/coralogix_managed_prometheus>`
- Learn about :doc:`common configuration options <metric-providers>`