EKS managed Prometheus
*************************

This guide walks you through integrating your EKS managed Prometheus with Robusta.

You will need to configure a pull integration that lets Robusta pull metrics from EKS Managed Prometheus.

Configure Pull Integration
===============================

1. Create an AWS access key, `See guide here <https://docs.aws.amazon.com/powershell/latest/userguide/pstools-appendix-sign-up.html>`_.

2. In your cluster, create a secret with your access key and secret access key, named `aws-secret-key`.

3. Collect the URL for your EKS managed Prometheus workspace.

4. Append the following to your `generated_values.yaml` file.

.. code-block:: yaml

  globalConfig:
  ...
    prometheus_url: EKS_PROMETHEUS_URL

  runner:
    additional_env_vars:
    - name: PROMETHEUS_SSL_ENABLED
      value: "true"
    - name: AWS_ACCESS_KEY
      value: <ACCESS KEY HERE>
    - name: AWS_ACCESS_KEY
      valueFrom:
        secretKeyRef:
          name: aws-secret-key
          key: <NAME_OF_ACCESS_KEY_KEY>
    - name: AWS_SECRET_ACCESS_KEY
      valueFrom:
        secretKeyRef:
          name: aws-secret-key
          key: <NAME_OF_SECRET_ACCESS_KEY_KEY>
    - name: AWS_SERVICE_NAME
      value: "aps" # <SERVICE NAME HERE>, it is usually aps
    - name: AWS_REGION
      value: <REGION_OF_WORKSPACE_HERE>
