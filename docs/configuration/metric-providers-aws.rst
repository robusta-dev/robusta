AWS Managed Prometheus
======================

Configure Robusta to use Amazon Managed Prometheus (AMP).

Prerequisites
-------------

1. An Amazon Managed Prometheus workspace
2. AWS access credentials (Access Key and Secret Key)

Quick Start
-----------

1. **Create AWS credentials** if you don't have them:
   
   Follow the `AWS guide <https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html#Using_CreateAccessKey>`_ to create an access key.

2. **Store credentials in Kubernetes**:

   .. code-block:: bash

       kubectl create secret generic aws-secret-key -n robusta \
           --from-literal=access-key=YOUR_ACCESS_KEY \
           --from-literal=secret-key=YOUR_SECRET_ACCESS_KEY

3. **Configure Robusta** - add to ``generated_values.yaml``:

   .. code-block:: yaml

       globalConfig:
           prometheus_url: "https://aps-workspaces.us-east-1.amazonaws.com/workspaces/ws-12345678"
           check_prometheus_flags: false  # Required for AWS
           
       runner:
           additional_env_vars:
           - name: PROMETHEUS_SSL_ENABLED
             value: "true"
           - name: AWS_ACCESS_KEY
             valueFrom:
               secretKeyRef:
                 name: aws-secret-key
                 key: access-key
           - name: AWS_SECRET_ACCESS_KEY
             valueFrom:
               secretKeyRef:
                 name: aws-secret-key
                 key: secret-key
           - name: AWS_SERVICE_NAME
             value: "aps"
           - name: AWS_REGION
             value: "us-east-1"  # Your workspace region

4. :ref:`Update Robusta <Simple Upgrade>`

Finding Your Workspace URL
--------------------------

1. Open the AWS Console
2. Navigate to Amazon Managed Service for Prometheus
3. Select your workspace
4. Copy the **Workspace endpoint URL**
5. Your prometheus_url is: ``<endpoint-url>``

Configuration Details
---------------------

**Required Environment Variables**:

- ``PROMETHEUS_SSL_ENABLED``: Always ``"true"`` for AMP
- ``AWS_SERVICE_NAME``: Always ``"aps"`` for Amazon Prometheus Service
- ``AWS_REGION``: The AWS region where your workspace is located

**Security Best Practices**:

1. Use IAM roles instead of access keys when possible
2. Limit access key permissions to AMP read operations only
3. Rotate credentials regularly

IAM Policy Example
------------------

Create an IAM policy with minimal permissions:

.. code-block:: json

    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "aps:QueryMetrics",
                    "aps:GetSeries",
                    "aps:GetLabels",
                    "aps:GetMetricMetadata"
                ],
                "Resource": "arn:aws:aps:*:*:workspace/*"
            }
        ]
    }


Important Notes
---------------

.. warning::

   AWS Managed Prometheus does not support the Prometheus flags API. Always set ``check_prometheus_flags: false``.

- AlertManager URL is not needed (AWS handles alerting separately)
- Ensure your AWS credentials have permissions to query the AMP workspace
- The workspace must be in the same region specified in AWS_REGION


Next Steps
----------

- Configure :doc:`alert routing </notification-routing/index>`
- Set up ingestion from your cluster to AMP
- Learn about :doc:`common configuration options <metric-providers>`