# Configuring Robusta with Grafana Cloud (Mimir)


This guide walks you through integrating Robusta with Grafana Cloud, enabling both the Robusta runner and Holmes to query metrics from Mimir and receive alerts from Grafana Cloud AlertManager.


## Step 1: Gather Grafana Cloud Information


### 1.1 Find Your Grafana Instance Details


1. Log into your Grafana Cloud portal
2. Note your Grafana instance URL (e.g., `https://YOUR-INSTANCE.grafana.net`)


### 1.2 Create API Keys


You'll need credentials For Grafana API Access (Robusta Runner and Holmes):


1. Go to **Administration → Service accounts**
2. Create a new service account named "robusta-integration"
3. Generate a service account token
4. Save the token (starts with `glsa_`)


### 1.3 Find Your Cluster Name in Prometheus


The cluster name is used to identify your specific cluster in Prometheus queries. To find it:


Check metrics with cluster labels in Grafana Explore:
  - Go to Grafana → Explore
  - Run query: `up{cluster!=""}`
  - Check the cluster label values. 
  - This will be set to `globalConfig.cluster_name` in `generated_values.yaml`


### 1.4 Find Datasource UIDs


1. Using the Grafana API, list your datasources:
```bash
curl -H "Authorization: Bearer YOUR_GLSA_TOKEN" \
 "https://YOUR-INSTANCE.grafana.net/api/datasources" | jq
```


2. Note the UIDs for:
  - Prometheus datasource UID (typically `grafanacloud-prom`)
  - AlertManager datasource UID (typically `grafanacloud-ngalertmanager`)


## Step 2: Configure Robusta Runner


### 2.1 Update Robusta Values (generated_values.yaml)


Your `generated_values.yaml`:


```yaml
globalConfig:
 # Your Robusta account details
 account_id: YOUR_ROBUSTA_ACCOUNT_ID
 signing_key: YOUR_ROBUSTA_SIGNING_KEY
  # Grafana Cloud Prometheus Configuration (via proxy)
 prometheus_url: https://YOUR-INSTANCE.grafana.net/api/datasources/proxy/uid/PROMETHEUS_DATASOURCE_UID
 prometheus_auth: Bearer YOUR_GLSA_TOKEN
  # Grafana Cloud AlertManager Configuration 
 alertmanager_url: https://YOUR-INSTANCE.grafana.net
 alertmanager_flavor: grafana
 alertmanager_auth: Bearer YOUR_GLSA_TOKEN
  # Grafana API Key for enrichments
 grafana_api_key: YOUR_GLSA_TOKEN
  # Cluster identification, necessary
 cluster_name: YOUR_CLUSTER_NAME
```


### 2.2 Apply Configuration


```bash
helm upgrade robusta robusta/robusta -f generated_values.yaml -n default
```


### 2.3 Restart Robusta Runner


```bash
kubectl rollout restart deployment/robusta-runner -n default
```


## Step 3: Configure Holmes Prometheus Toolset


### 3.1 Update Holmes Configuration


Add to your `generated_values.yaml` under the `holmes` section:


```yaml
holmes:
 enableHolmesGPT: true
 additionalEnvVars:
   - name: MODEL
     value: YOUR_LLM_MODEL  # e.g., gpt-4o, azure/gpt-4o
  
 # Holmes-specific toolsets configuration
 toolsets:
   prometheus/metrics:
     enabled: true
     config:
       prometheus_url: https://YOUR-INSTANCE.grafana.net/api/datasources/proxy/uid/PROMETHEUS_DATASOURCE_UID
       fetch_labels_with_labels_api: False
       fetch_metadata_with_series_api: True
       headers:
         Authorization: Bearer YOUR_GLSA_TOKEN
         # X-Scope-Org-Id is usually not needed when using proxy endpoint
         # X-Scope-Org-Id: "1" replace with the correct org id: 


```


### 3.2 Apply Holmes Configuration


```bash
helm upgrade robusta robusta/robusta -f generated_values.yaml -n default
kubectl rollout restart deployment/robusta-holmes -n default
```





