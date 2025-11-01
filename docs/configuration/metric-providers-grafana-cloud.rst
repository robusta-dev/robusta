Grafana Cloud (Mimir)
=====================

Configure Robusta to use Grafana Cloud's managed Prometheus (Mimir) for querying metrics.

Prerequisites
-------------

* A Grafana Cloud account with a configured instance
* Prometheus datasource configured in Grafana Cloud
* Access to create service accounts and API tokens

Quick Start
-----------

1. **Find Your Grafana Instance URL**:

   Log into your Grafana Cloud portal and note your instance URL (e.g., ``https://YOUR-INSTANCE.grafana.net``).

2. **Create API Token**:

   - Go to **Administration → Service accounts**
   - Create a new service account named "robusta-integration"
   - Generate a service account token
   - Save the token (starts with ``glsa_``)

3. **Find Datasource UID**:

   Using the Grafana API, list your datasources:

   .. code-block:: bash

       curl -H "Authorization: Bearer YOUR_GLSA_TOKEN" \
         "https://YOUR-INSTANCE.grafana.net/api/datasources" | jq

   Note the UID for your Prometheus datasource (typically ``grafanacloud-prom``).

4. **Find Your Cluster Name** (if using multi-cluster setup):

   - Go to Grafana → Explore
   - Run query: ``up{cluster!=""}``
   - Note the cluster label value

5. **Add to your** ``generated_values.yaml``:

   .. code-block:: yaml

       globalConfig:
           # Grafana Cloud Prometheus Configuration (via proxy)
           prometheus_url: https://YOUR-INSTANCE.grafana.net/api/datasources/proxy/uid/PROMETHEUS_DATASOURCE_UID
           prometheus_auth: Bearer YOUR_GLSA_TOKEN

           # Grafana API Key for enrichments and silencing
           grafana_api_key: YOUR_GLSA_TOKEN
           grafana_url: https://YOUR-INSTANCE.grafana.net

           # Grafana Cloud AlertManager Configuration
           alertmanager_url: https://YOUR-INSTANCE.grafana.net
           alertmanager_flavor: grafana
           alertmanager_auth: Bearer YOUR_GLSA_TOKEN

       # Cluster identification (required for multi-cluster)
       clusterName: YOUR_CLUSTER_NAME

   .. note::

       **Optional:** To create silences from Robusta, the Grafana API key must have the ``Editor`` role.

6. :ref:`Update Robusta <Simple Upgrade>`

Multi-cluster Setup
-------------------

Make sure ``clusterName`` in Robusta Helm's values matches the ``cluster`` label in Grafana.

.. code-block:: yaml

    clusterName: "production-us-east"

HolmesGPT Configuration
-----------------------

Give HolmesGPT - Robusta's AI Agent - read access to metrics. See the `Grafana Cloud (Mimir) Configuration <https://holmesgpt.dev/data-sources/builtin-toolsets/prometheus/?h=prometheus#grafana-cloud-mimir-configuration>`_ guide.

Next Steps
----------

- :doc:`Send alerts from Grafana Cloud to Robusta </configuration/alertmanager-integration/grafana-cloud>`
