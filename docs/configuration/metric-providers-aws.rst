AWS Managed Prometheus
======================

Configure Robusta to use Amazon Managed Prometheus (AMP).

Prerequisites
-------------

Before configuring Robusta with AWS Managed Prometheus, ensure you have:

1. **An Amazon Managed Prometheus (AMP) workspace**  
   See: `Getting started with Amazon Managed Service for Prometheus <https://docs.aws.amazon.com/prometheus/latest/userguide/AMP-getting-started.html>`_.

2. **For IRSA**: Your EKS cluster must have an OIDC identity provider configured.  
   See: `Associate IAM OIDC Provider <https://docs.aws.amazon.com/eks/latest/userguide/enable-iam-roles-for-service-accounts.html>`_.

3. **AWS access credentials (Access Key and Secret Key)**  
   With sufficient permissions to query AMP (for example, the ``AmazonPrometheusQueryAccess`` policy).

IRSA (Recommended)
------------------

IRSA (IAM Roles for Service Accounts) is the recommended way to authenticate Robusta with AWS Managed Prometheus.  
With IRSA, you don’t need to manage long-lived AWS access keys — credentials are securely provided to pods via Kubernetes service accounts.

.. dropdown:: AWS Setup for IRSA
   :animate: fade-in-slide-down

   1. **Ensure your EKS cluster has an OIDC provider associated**:  
      See the AWS guide: `Associate IAM OIDC Provider <https://docs.aws.amazon.com/eks/latest/userguide/enable-iam-roles-for-service-accounts.html>`_.

   2. **Create an IAM role for Prometheus access with the correct trust policy**:  
      The role must include:

      - The managed policy ``AmazonPrometheusQueryAccess`` (or equivalent custom policy).
      - A trust policy allowing ``sts:AssumeRoleWithWebIdentity`` from your cluster’s OIDC provider.

      Example trust policy (replace placeholders accordingly):

      .. code-block:: json

         {
           "Version": "2012-10-17",
           "Statement": [
             {
               "Effect": "Allow",
               "Principal": {
                 "Federated": "arn:aws:iam::<ACCOUNT_ID>:oidc-provider/oidc.eks.<REGION>.amazonaws.com/id/<OIDC_ID>"
               },
               "Action": "sts:AssumeRoleWithWebIdentity",
               "Condition": {
                 "StringEquals": {
                   "oidc.eks.<REGION>.amazonaws.com/id/<OIDC_ID>:sub": "system:serviceaccount:<NAMESPACE>:<SERVICE_ACCOUNT_NAME>"
                 }
               }
             }
           ]
         }

Quick Start
~~~~~~~~~~~

1. **Configure Robusta** - update the ``generated_values.yaml`` file with the required settings, ensuring you include the correct IRSA-related annotations.

   .. code-block:: yaml

       holmes:
         serviceAccount:
           annotations:
             eks.amazonaws.com/role-arn: arn:aws:iam::<ACCOUNT_ID>:role/<AMP_IAM_ROLE>
         toolsets:
           prometheus/metrics:
             enabled: true
             config:
               prometheus_url:  "https://aps-example-workspace.us-east-1.amazonaws.com/workspaces/ws-12345678"
               aws_region: us-east-1
               aws_service_name: aps
               prometheus_ssl_enabled: true
               additional_labels: # Add cluster label to all queries
                 cluster: my_cluster_name
              # Optional: Configure cross-account role assumption for AMP
              # Set assume_role_arn if your Prometheus workspace is in a different AWS account
              # than the one running your Kubernetes service account.
              # assume_role_arn: arn:aws:iam::<ACCOUNT_ID>:role/<AMP_IAM_ROLE>

       runnerServiceAccount:
         annotations:
           eks.amazonaws.com/role-arn: arn:aws:iam::<ACCOUNT_ID>:role/<AMP_IAM_ROLE>
       globalConfig:
         prometheus_url: "https://aps-example-workspace.us-east-1.amazonaws.com/workspaces/ws-12345678"
         check_prometheus_flags: false  # Required for AWS
         prometheus_additional_labels: # Add cluster label to all queries
           cluster: 'my_cluster_name'
       runner:
         additional_env_vars:
         - name: PROMETHEUS_SSL_ENABLED
           value: "true"
         - name: AWS_SERVICE_NAME
           value: "aps"
         - name: AWS_REGION
           value: "us-east-1"  # Your workspace region
        # Optional: Configure cross-account role assumption for AMP
        # Set this if your Prometheus workspace is in a different AWS account
        # than the one running your Kubernetes service account.
        # - name: AWS_ASSUME_ROLE
        #   value: "arn:aws:iam::<ACCOUNT_ID>:role/<AMP_IAM_ROLE>"

2. :ref:`Update Robusta <Simple Upgrade>`

Access Keys (Alternative)
-------------------------

If you prefer not to use IRSA, you can authenticate with long-lived AWS access keys.

.. dropdown:: AWS Setup for Access Keys
   :animate: fade-in-slide-down
   :icon: key

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
~~~~~~~~~~~~~~~~~~~~~~~~~~

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

Important Notes
---------------

.. warning::

   AWS Managed Prometheus does not support the Prometheus flags API. Always set ``check_prometheus_flags: false``.

- AlertManager URL is not needed (AWS handles alerting separately)
- Ensure your IAM role or AWS credentials have permissions to query the AMP workspace
- The workspace must be in the same region specified in AWS_REGION

Next Steps
----------

- Configure :doc:`alert routing </notification-routing/index>`
- Set up ingestion from your cluster to AMP
- Learn about :doc:`common configuration options <metric-providers>`
