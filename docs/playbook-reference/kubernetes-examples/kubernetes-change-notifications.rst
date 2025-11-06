Change Tracking Playbooks
################################

You can configure Robusta to send push notifications when Kubernetes resources change or become unhealthy. This is done by listening to API Server changes with `kubewatch <https://github.com/robusta-dev/kubewatch/>`_ and then filtering the stream of events in a Robusta playbook.

Notifications are sent to configured :ref:`Sinks <sinks-reference>` like Slack or MSTeams. You can also :ref:`route notifications to specific sinks<Routing Alerts to Specific Sinks>`.

Pod Health Tracking
===================

Failed Liveness Probes
----------------------

Get notified when liveness probes fail.

Add the following YAML to the ``customPlaybooks`` Helm value:

.. code-block:: yaml

    customPlaybooks:
    - triggers:
        - on_kubernetes_warning_event_create:
            include: ["Liveness"]
      actions:
        - create_finding:
            aggregation_key: "Failed Liveness Probe"
            severity: HIGH
            title: "Failed liveness probe: $name"
        - event_resource_events: {}

Then do a :ref:`Helm Upgrade <Simple Upgrade>`.

.. details:: Testing

    Apply the following command to create a failing liveness probe:

    .. code-block:: bash

        kubectl apply -f https://raw.githubusercontent.com/robusta-dev/kubernetes-demos/main/liveness_probe_fail/failing_liveness_probe.yaml

    You should get a notification in your configured sink.

    .. image:: /images/failedlivenessprobe.png
        :alt: Failed liveness probe notification on Slack
        :align: center

.. details:: How it Works

    This playbook uses the :ref:`on_kubernetes_warning_event_create<on_kubernetes_warning_event_create>` trigger, which fires for Liveness probe failures in your cluster.

    It uses the :ref:`create_finding <create_finding>` action to generate a notification message, and :ref:`event_resource_events <event_resource_events>` action to gather all other events on the same resource in the near past.


Job Tracking
============

Failed Kubernetes Jobs
-----------------------

Get notified about failed Kubernetes Jobs.

.. image:: /images/failingjobs.png
    :alt: Failing Kubernetes jobs notification on Slack
    :align: center

.. admonition:: Avoid Duplicate Alerts

    If you installed Robusta with the embedded Prometheus stack, you don't need to configure this playbook. It's configured by default.

Add the following YAML to the ``customPlaybooks`` Helm value:

.. code-block:: yaml

    customPlaybooks:
    - triggers:
      - on_job_failure: {}
      actions:
      - create_finding:
          title: "Job Failed"
          aggregation_key: "JobFailure"
      - job_info_enricher: {}
      - job_events_enricher: {}
      - job_pod_enricher: {}

Then do a :ref:`Helm Upgrade <Simple Upgrade>`.

.. details:: Testing

    Deploy a failing job. The job will fail after 60 seconds, then attempt to run again. After two attempts, it will fail for good.

    .. code-block:: bash

        kubectl apply -f https://raw.githubusercontent.com/robusta-dev/kubernetes-demos/main/job_failure/job_crash.yaml

.. details:: How it Works

    * :ref:`on_job_failure<on_job_failure>` fires once for each failed Kubernetes Job
    * :ref:`create_finding<create_finding>` generates a notification message
    * :ref:`job_info_enricher<job_info_enricher>` fetches the Jobs status and information
    * :ref:`job_events_enricher<job_events_enricher>` runs ``kubectl get events``, finds Events related to the Job, and attaches them
    * :ref:`job_pod_enricher<job_pod_enricher>` finds Pods that were part of the Job. It attaches Pod-level information like Pod logs



Workload Change Tracking
=========================

Track changes to Deployments and other workload resources. You can filter specific YAML fields to avoid noise - for example, ignoring ``spec.replicas`` changes from autoscaling.

Deployment Image Changes
------------------------

Get notified when a Deployment strategy or container details change.

Add the following YAML to the ``customPlaybooks`` Helm value:

.. code-block:: yaml

    customPlaybooks:
    - triggers:
        - on_deployment_update:
            change_filters:
              ignore:
              - status
              - metadata.generation
              - metadata.resourceVersion
              - metadata.managedFields
              - spec.replicas
              include:
                - spec.template.spec.containers[0]
                - spec.strategy
      actions:
        - resource_babysitter: {}
        - customise_finding:
            severity: HIGH
            title: "New changes in $kind/$namespace/$name"
      sinks:
        - some_sink_name # Optional

Then perform a :ref:`Helm Upgrade <Simple Upgrade>`.

**Note**: You can also use :ref:`Sink Matchers<sink-matchers>` to route notifications instead of explicitly specifying a sink in the playbook.

.. details:: Testing

    Modify the image of a deployment in your cluster.

    Run the following YAML files to simulate a deployment image change:

    .. code-block:: bash

        kubectl apply -f https://raw.githubusercontent.com/robusta-dev/kubernetes-demos/main/deployment_image_change/before_image_change.yaml
        kubectl apply -f https://raw.githubusercontent.com/robusta-dev/kubernetes-demos/main/deployment_image_change/after_image_change.yaml

    A Robusta notification will arrive in your configured :ref:`sinks <sinks-reference>`, showing exactly what changed in the deployment.

    .. image:: /images/deployment-image-change.png
      :width: 600
      :align: center

.. details:: How it Works

    1. The ``on_deployment_update`` trigger monitors deployment changes
    2. ``change_filters`` specify which fields to monitor, ignoring noisy fields like ``spec.replicas`` that change due to autoscaling
    3. Optionally route notifications to specific sinks


Deployment Manifest on Image Change
------------------------------------

Get the full Deployment manifest sent to a webhook each time the image changes.

Add the following YAML to the ``customPlaybooks`` Helm value:

.. code-block:: yaml

    customPlaybooks:
    - triggers:
      - on_deployment_update:
          change_filters:
            include:
            - image
      actions:
      - json_change_tracker:
          url: "https://SOME-WEBHOOK-URL"

This playbook doesn't use a Sink - it sends the manifest as JSON to the webhook URL specified in the action parameters.

Then perform a :ref:`Helm Upgrade <Simple Upgrade>`.

.. details:: Testing

    Modify a Deployment image in your cluster.

    A notification with the Deployment manifest, as JSON, should be sent to the webhook URL.


Network Resource Tracking
==========================

Ingress Changes
---------------

Get notified when Ingress rules or TLS details change.

Add the following YAML to the ``customPlaybooks`` Helm value:

.. code-block:: yaml

    customPlaybooks:
    - triggers:
        - on_ingress_all_changes:
            change_filters:
              ignore:
                - status
                - metadata.generation
                - metadata.resourceVersion
                - metadata.managedFields
                - spec.replicas
              include:
                - spec.rules
                - spec.tls
      actions:
        - resource_babysitter: {}
      sinks:
        - some_sink_name # Optional

Then perform a :ref:`Helm Upgrade <Simple Upgrade>`.

**Note**: You can also use :ref:`Sink Matchers<sink-matchers>` to route notifications instead of explicitly specifying a sink in the playbook.

.. details:: Testing

    Create, modify, or delete an ingress in your cluster.

    Run the following commands to simulate ingress changes:

    .. code-block:: bash

        kubectl apply -f https://raw.githubusercontent.com/robusta-dev/kubernetes-demos/main/ingress_port_path_change/before_port_path_change.yaml
        kubectl apply -f https://raw.githubusercontent.com/robusta-dev/kubernetes-demos/main/ingress_port_path_change/after_port_path_change.yaml

    A Robusta notification will arrive in your configured :ref:`sinks <sinks-reference>`, showing exactly what changed in the ingress.

    .. image:: /images/ingress-image-change.png
      :width: 600
      :align: center

.. details:: How it Works

    1. The ``on_ingress_all_changes`` trigger monitors all ingress changes
    2. ``change_filters`` specify to only notify on ``spec.rules`` and ``spec.tls`` changes
    3. Optionally route notifications to specific sinks


Secret Tracking
===============

.. _track-secrets-overview:

Track Kubernetes Secret Changes
--------------------------------

By default Robusta is not configured to track secret changes. To enable secret tracking, you need to grant permissions to Robusta and configure kubewatch.

**Setup Steps**:

1. **Grant Permissions to Robusta**: By default, Robusta does not have permission to read Secrets
2. **Configure Kubewatch**: Set up Kubewatch to monitor Secret resources
3. **Create Custom Playbook**: Define notification rules

**1. Grant Permissions to Robusta**

Create a YAML file named ``kubewatch-secret-permissions.yaml`` with the following content:

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

.. code-block:: bash

    kubectl apply -f kubewatch-secret-permissions.yaml

**2. Configure Kubewatch to Monitor Secrets**

Add the following to the ``kubewatch`` section in your ``generated_values.yaml``:

.. code-block:: yaml

    kubewatch:
      config:
        namespace: your-namespace
        resource:
          secret: true

**3. Create Custom Playbook**

Add the following to the ``customPlaybooks`` section in your ``generated_values.yaml``:

.. code-block:: yaml

    customPlaybooks:
    - triggers:
        - on_secret_all_changes: {}
      actions:
        - create_finding:
            title: "Secret $name in namespace $namespace was changed"
            aggregation_key: SecretModified

Then perform a :ref:`Helm Upgrade <Simple Upgrade>`.

**Note**: You can also use :ref:`Sink Matchers<sink-matchers>` to route notifications instead of explicitly specifying a sink in the playbook.

.. details:: Testing

    1. **Create a Test Secret**:

       .. code-block:: bash

           kubectl create secret generic test-secret --from-literal=key1=value1

    2. **Modify the Secret**:

       .. code-block:: bash

           kubectl patch secret test-secret -p '{"stringData":{"key1":"newvalue"}}'

    3. **Delete the Secret**:

       .. code-block:: bash

           kubectl delete secret test-secret

    A Robusta notification will arrive in your configured :ref:`sinks <sinks-reference>`, indicating that the Secret was created, modified, or deleted.

.. details:: How it Works

    1. **Grant Permissions**: The RBAC YAML grants Robusta the necessary permissions to read Secrets
    2. **Configure Kubewatch**: The ``kubewatch`` configuration tells Robusta to monitor Secret resources
    3. **Set Up the Trigger**: The ``on_secret_all_changes`` trigger ensures you'll receive notifications for all Secret changes
    4. **Create the Notification**: The ``create_finding`` action generates a notification with a custom title
