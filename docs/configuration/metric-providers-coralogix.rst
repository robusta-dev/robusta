Coralogix
=========

Configure Robusta to use Coralogix's managed Prometheus service.

Quick Start
==============================

Metrics querying lets Robusta pull metrics from Coralogix Managed Prometheus.

1. Go to `Coralogix Documentation <https://coralogix.com/docs/integrations/coralogix-endpoints/#promql>`_ and choose the relevant 'PromQL Endpoint' from their table.
2. In your `generated_values.yaml` file add the endpoint url:

.. code-block:: yaml

  # this line should already exist
  globalConfig:
      prometheus_url: "<YOUR_PROM_API_LINK_HERE>" #for example https://prom-api.coralogix.com
      # To add any labels that are relevant to the specific cluster uncomment and change the lines below (optional)
      # prometheus_additional_labels:
      #   cluster: 'CLUSTER_NAME_HERE'



3. On the Coralogix site, go to Data Flow -> Api Keys and copy the 'Logs Query Key'

.. note:: If one does not exist you will have to generate a new one by clicking 'GENERATE NEW API KEY'

4. Create a secret in your cluster with your key logs_query_key and the value as the key you just copied

5. In your generated_values.yaml file add the following environment variables from the previous step replacing MY_CORLOGIX_SECRET with your secret name.

.. code-block:: yaml

  runner:
    additional_env_vars:
    - name: PROMETHEUS_SSL_ENABLED
      value: "true"
    - name: CORALOGIX_PROMETHEUS_TOKEN
      valueFrom:
        secretKeyRef:
          name: MY_CORALOGIX_SECRET
          key: logs_query_key

Then :ref:`update Robusta <Simple Upgrade>`.

Next Steps
----------

- Configure :doc:`alert routing </notification-routing/index>`
- Set up :doc:`Coralogix alerts integration </configuration/alertmanager-integration/coralogix_managed_prometheus>`
- Learn about :doc:`common configuration options <metric-providers>`