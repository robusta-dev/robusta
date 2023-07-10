Corlogix managed Prometheus
*************************

Get the Corlogix prometheus query endpoint
=========================================

1. Go to `Corlogix Documentation <https://coralogix.com/docs/grafana-plugin/#block-1778265e-61c2-4362-9060-533d158857d7>`_ and choose the relevant PromQL Endpoint.
2. In your `generated_values.yaml` file add the endpoint url:

.. code-block:: yaml

  # this line should already exist
  globalConfig:
      prometheus_url: "<YOUR_PROM_API_LINK_HERE>" #for example https://prom-api.coralogix.com

Set up the key to Query Corlogix Prometheus
==============================================

We will get you the key for robusta to query corlogix managed prometheus

1. On the corlogix site, go to Data Flow -> Api Keys and copy the Logs Query Key

.. note:: If one does not exist you will have to generate a new one by clicking 'GENERATE NEW API KEY'

2. Create a secret in your cluster with your key logs_query_key and the value as the key you just copied

2. In your generated_values.yaml file add the following environment variables from the previous step replacing MY_CORLOGIX_SECRET with your secret name.

.. code-block:: yaml

  runner:
    additional_env_vars:
    - name: CORLOGIX_PROMETHEUS_TOKEN
      valueFrom:
        secretKeyRef:
          name: MY_CORLOGIX_SECRET
          key: logs_query_key

