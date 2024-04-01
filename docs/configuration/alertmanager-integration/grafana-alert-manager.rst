Grafana AlertManager
****************************************

Grafana can send alerts to Robusta for automatic enrichment and visualization.

.. image:: /images/grafana-docs-robusta-ui.png
  :width: 600
  :align: center


This guide only covers integrating alerts from Grafana Alerting with Robusta, not configuring Robusta to query metrics from the relevant Grafana data source.

After completing this tutorial, we recommend configuring a metrics integration according to the :ref:`standard instructions for your metrics backend <Integrating with Prometheus>`

Prerequisite
=================================
* A label in the following format ``cluster_name: YourClusterName`` added to each alert, with the cluster name as it appears in Robusta ``generated_values.yaml``.

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
4. Enter your ``<account_id> <signing_key>`` in the ``Authorization Headers - Credentials`` box (locate this in your generated_values.yaml file).

   For example, if ``account_id: f88debc9-68b9-4c2a-e372-e948941518d2`` and ``signing_key: be48413c-e23f-b648-c6b5-773739a377f7``, then use ``f88debc9-68b9-4c2a-e372-e948941518d2 be48413c-e23f-b648-c6b5-773739a377f7`` as the value.

.. image:: /images/grafana-alertmanager-post.png
  :width: 600
  :align: center

5. Click "Test" button. Select "custom" and add a ``cluster_name`` label to send a test alert (Robusta requires every alert has this ``cluster_name`` label).

.. image:: /images/grafana-alertmanager-test.png
  :width: 600
  :align: center

If successful, you will receive a notification in the Robusta UI, Slack or any other destination configured in Robusta, such as Microsoft Teams.

.. image:: /images/grafana-alertmanager-robusta-ui.png
  :width: 600
  :align: center

6. Finally, click "Save contact point" to complete the Robusta integration.


Configure Silencing
=================================================

Modify and add the following config to ``generated_values.yaml`` and :ref:`update Robusta <Simple Upgrade>`.

.. code-block:: yaml

    globalConfig: # this line should already exist
        # add the lines below
        grafana_url: "https://<grafana url>.grafana.net"
        # Create alert silencing when using Grafana alerts
        grafana_api_key: <YOUR GRAFANA EDITOR API KEY>
        alertmanager_flavor: grafana # (1)

        # alertmanager_url: "https://alertmanager<url>.grafana.net"
        # prometheus_url: "https://prometheus<url>.grafana.net/api/prom"

        # Add any labels that are relevant to the specific cluster (optional)
        # prometheus_additional_labels:
        #   cluster: 'CLUSTER_NAME_HERE'

.. code-annotations::
    1. This is necessary for Robusta to create silences when using Grafana Alerts, because of minor API differences in the AlertManager embedded in Grafana.

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
