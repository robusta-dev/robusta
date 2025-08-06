.. _track-secrets-overview:

Track Kubernetes Secret Changes
############################################

By default Robusta is not configured to track secret changes, but it is possible to configure it
by giving permissions to Robusta to read secrets and configuring kubewatch.

How to Track Changes in Kubernetes Secrets
------------------------------------------------

1. **Grant Permissions to Robusta**: By default, Robusta does not have permission to read Secrets. You'll need to grant it the necessary permissions.
2. **Configure Kubewatch**: Set up Kubewatch to monitor Secret resources.
3. **Create Custom Playbook**: Define a playbook that specifies when you should be notified and what data you'd like to see.
4. **Route Alerts (Optional)**: If needed, direct these notifications to specific destinations, also known as 'Sinks', by adding this information to your custom playbook.

Updating Configurations to track Secret Changes
*******************************************************
**Scenario**: You want to be notified whenever a Secret in your cluster is created, updated, or deleted.

**Implementation**:

Add the following configurations to your `generated_values.yaml` file and apply the necessary permissions.

**1. Grant Permissions to Robusta**

Create a YAML file named `kubewatch-secret-permissions.yaml` with the following content:

.. code-block:: yaml

    apiVersion: rbac.authorization.k8s.io/v1
    kind: ClusterRole
    metadata:
      namespace: your-namespace
      name: read-secrets-role
    rules:
    - apiGroups: [""]
      resources: ["secrets"]
      verbs: ["get", "list", "watch"]
    ---
    apiVersion: rbac.authorization.k8s.io/v1
    kind: ClusterRoleBinding
    metadata:
      name: read-secrets-role-binding
    subjects:
    - kind: ServiceAccount
      name: robusta-forwarder-service-account
      namespace: your-namespace
    roleRef:
      kind: ClusterRole
      name: read-secrets-role
      apiGroup: rbac.authorization.k8s.io

Apply the permissions:

.. code-block:: shell

    kubectl apply -f kubewatch-secret-permissions.yaml

**2. Configure Kubewatch to Monitor Secrets**

Add the following to the `kubewatch` section in your `generated_values.yaml`:

.. code-block:: yaml

    kubewatch:
      config:
        namespace: your-namespace
        resource:
          secret: true

**3. Create Custom Playbook**

Add the following to the `customPlaybooks` section in your `generated_values.yaml`:

.. code-block:: yaml

    customPlaybooks:
    - triggers:
        - on_secret_all_changes: {}
      actions:
        - create_finding:
            title: "Secret $name in namespace $namespace was changed"
            aggregation_key: SecretModified

.. details:: How does it work?

  1. **Grant Permissions**: The first YAML grants Robusta the necessary permissions to read Secrets.
  2. **Configure Kubewatch**: The `kubewatch` configuration tells Robusta to monitor Secret resources.
  3. **Set Up the Trigger**: The `on_secret_all_changes` trigger ensures you'll receive notifications for all Secret changes.
  4. **Create the Notification**: The `create_finding` action generates a notification with a custom title.

Then perform a :ref:`Helm Upgrade <Simple Upgrade>`.

**Note**: You can also use the :ref:`Sink Matchers<sink-matchers>` to route notifications instead of explicitly specifying a sink in the playbook.

**Testing**:

1. **Create a Test Secret**:

   .. code-block:: shell

       kubectl create secret generic test-secret --from-literal=key1=value1

2. **Modify the Secret**:

   .. code-block:: shell

       kubectl patch secret test-secret -p '{"stringData":{"key1":"newvalue"}}'

3. **Delete the Secret**:

   .. code-block:: shell

       kubectl delete secret test-secret

A Robusta notification will arrive in your configured :ref:`sinks <Sinks Reference>`, indicating that the Secret was created, modified, or deleted.


Cleanup
------------------------------

To stop monitoring Secret changes:

1. Remove the playbook you added from the `customPlaybooks` in your `generated_values.yaml` file.
2. Remove the Secret monitoring configuration:

   .. code-block:: yaml

       kubewatch:
         config:
           resource:
             secret: false

3. Delete the permissions:

   .. code-block:: shell

       kubectl delete -f kubewatch-secret-permissions.yaml

Then, perform a :ref:`Helm Upgrade <Simple Upgrade>`.
