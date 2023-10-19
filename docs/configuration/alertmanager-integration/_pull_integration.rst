Configure Pull Integration
====================================

A pull integration lets Robusta pull metrics and create silences.

To configure it, add the following to ``generated_values.yaml`` and :ref:`update Robusta <Simple Upgrade>`.

.. code-block:: yaml

    globalConfig: # this line should already exist
        # add the lines below
        alertmanager_url: "http://ALERT_MANAGER_SERVICE_NAME.NAMESPACE.svc.cluster.local:9093" # (1)
        grafana_url: ""

        prometheus_url: "http://PROMETHEUS_SERVICE_NAME.NAMESPACE.svc.cluster.local:9090" # (2)

        # Add any labels that are relevant to the specific cluster (optional)
        # prometheus_additional_labels:
        #   cluster: 'CLUSTER_NAME_HERE'

        # Create alert silencing when using Grafana alerts (optional)
        # grafana_api_key: <YOUR GRAFANA EDITOR API KEY> # (3)
        # alertmanager_flavor: grafana

.. code-annotations::
    1. Example: http://alertmanager-Helm_release_name-kube-prometheus-alertmanager.default.svc.cluster.local:9093.
    2. Example: http://Helm_Release_Name-kube-prometheus-prometheus.default.svc.cluster.local:9090
    3. This is necessary for Robusta to create silences when using Grafana Alerts, because of minor API differences in the AlertManager embedded in Grafana.

You can optionally setup authentication, SSL verification, and other parameters described below.

Verify it Works
^^^^^^^^^^^^^^^^^
Open any application in the Robusta UI. If CPU and memory graphs are shown, everything is working.

If you don't use the Robusta UI, trigger a `demo OOMKill alert <https://github.com/robusta-dev/kubernetes-demos/#oomkilled-pod-out-of-memory-kill>`_,
and verify that Robusta sends a Slack/Teams message with a memory graph included. If so, everything is configured properly.

Optional Settings
^^^^^^^^^^^^^^^^^^

Authentication Headers
-----------------------

If Prometheus and/or AlertManager require authentication, add the following to ``generated_values.yaml``:

.. code-block:: yaml

  globalConfig:
    prometheus_auth: Bearer <YOUR TOKEN> # Replace <YOUR TOKEN> with your actual token or use any other auth header as needed
    alertmanager_auth: Basic <USER:PASSWORD base64-encoded> # Replace <USER:PASSWORD base64-encoded> with your actual credentials, base64-encoded, or use any other auth header as needed

The two settings may be configured independently.

SSL Verification
-----------------------
By default, Robusta does not verify the SSL certificate of the Prometheus server.

To enable SSL verification, add the following to Robusta's ``generated_values.yaml``:

.. code-block:: yaml

  runner:
    additional_env_vars:
    - name: PROMETHEUS_SSL_ENABLED
      value: "true"

If you have a custom Certificate Authority (CA) certificate, add one more setting:

.. code-block:: yaml

  runner:
    certificate: "<YOUR BASE-64 ENCODED DATA>" # base64-encoded certificate value
