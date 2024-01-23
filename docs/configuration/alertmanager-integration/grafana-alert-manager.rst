Grafana AlertManager
****************************************

Using Grafana alerts involves a `special instance of AlertManager embedded within Grafana <https://grafana.com/docs/grafana/latest/alerting/fundamentals/alertmanager/>`_.
.. image:: /images/grafana-alertmanager-save-contact-point.png
  :width: 600
  :align: center

You need to configure two integrations: one to send alerts to Robusta and another to let Robusta query metrics and create silences.

Prerequisite
=================================
* A ``cluster_name: YourClusterName`` label for each cluster.

Send Alerts to Robusta
============================

This integration lets you send Grafana alerts to Robusta.

To configure it:

1. In the Grafana UI, navigate to the ``Alerting`` tab, click on ``Add contact point``, and select ``Webhook`` from the Integration options.

.. image:: /images/grafana-alertmanager-contact-point.png
  :width: 600
  :align: center

2. Insert the following URL:

.. code-block::

    https://api.robusta.dev/integrations/generic/alertmanager

.. image:: /images/grafana-alertmanager-url.png
  :align: center

3. Change the HTTP Method to POST in the ``Optional Webhook Settings``.
4. Enter your "Account_id Signing_key" in the ``Authorization Headers - Credentials`` box (locate this in your generated_values.yaml file).

.. image:: /images/grafana-alertmanager-post.png
  :width: 600
  :align: center

5. Click "Test", if you already have the ``cluster_name`` label, your notification should go through. If not, try using the custom label option. A notification should arrive at Robusta UI or Slack/MSTeams if configured correctly.

.. image:: /images/grafana-alertmanager-test.png
  :width: 600
  :align: center

6. Finally, click "Save contact point" to complete the Robusta integration.




Configure Querying and Silencing
=================================================

To configure metrics querying and creating silences, add the following to ``generated_values.yaml`` and :ref:`update Robusta <Simple Upgrade>`.

.. code-block:: yaml

    globalConfig: # this line should already exist
        # add the lines below
        alertmanager_url: "http://ALERT_MANAGER_SERVICE_NAME.NAMESPACE.svc.cluster.local:9093" # (1)
        grafana_url: ""

        prometheus_url: "http://PROMETHEUS_SERVICE_NAME.NAMESPACE.svc.cluster.local:9090" # (2)


        # Create alert silencing when using Grafana alerts (optional)
        grafana_api_key: <YOUR GRAFANA EDITOR API KEY> # (3)
        alertmanager_flavor: grafana

        # Add any labels that are relevant to the specific cluster (optional)
        # prometheus_additional_labels:
        #   cluster: 'CLUSTER_NAME_HERE'

.. code-annotations::
    1. Replace with actual service name, e.g., http://alertmanager-Helm_release_name-kube-prometheus-alertmanager.default.svc.cluster.local:9093.
    2. Replace with actual service name, e.g., http://Helm_Release_Name-kube-prometheus-prometheus.default.svc.cluster.local:9090
    3. This is necessary for Robusta to create silences when using Grafana Alerts, because of minor API differences in the AlertManager embedded in Grafana.

.. note::

  The Grafana API key must have the ``Editor`` role in order to create silences.


You can optionally set up authentication, SSL verification, and other parameters described below.

Verify it Works
^^^^^^^^^^^^^^^^^
Open any application in the Robusta UI. If CPU and memory graphs are shown, everything is working.

Alternatively, trigger a `demo OOMKill alert <https://github.com/robusta-dev/kubernetes-demos/?tab=readme-ov-file#simple-scenarios>`_ and confirm that Robusta sends a Slack/Teams message with a memory graph. This indicates proper configuration.


Optional Settings
=============================

Authentication Headers
^^^^^^^^^^^^^^^^^^^^^^^^^^

If Prometheus and/or AlertManager require authentication, add the following to ``generated_values.yaml``:

.. code-block:: yaml

  globalConfig:
    prometheus_auth: Bearer <YOUR TOKEN> # Replace <YOUR TOKEN> with your actual token or use any other auth header as needed
    alertmanager_auth: Basic <USER:PASSWORD base64-encoded> # Replace <USER:PASSWORD base64-encoded> with your actual credentials, base64-encoded, or use any other auth header as needed

These settings may be configured independently.

SSL Verification
^^^^^^^^^^^^^^^^^^^^
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
