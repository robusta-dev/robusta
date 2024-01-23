Grafana AlertManager
****************************************

Using Grafana alerts involves a `special instance of AlertManager embedded within Grafana <https://grafana.com/docs/grafana/latest/alerting/fundamentals/alertmanager/>`_.

.. image:: /images/grafana-alertmanager-save-contact-point.png
  :width: 600
  :align: center

You need to configure two integrations: one to send alerts to Robusta and another to allow Robusta query metrics and create silences.

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

.. image:: /images/grafana-alertmanager-post.png
  :width: 600
  :align: center

5. Click "Test" button. Select "custom" and add a ``cluster_name`` label to send a test alert (Robusta requires every alert has this ``cluster_name`` label).

.. image:: /images/grafana-alertmanager-test.png
  :width: 600
  :align: center

If everything worked, a notification should arrive in a Robusta UI stack or whatever destinations Robusta is connected to like stack MS teams.

.. image:: /images/grafana-alertmanager-robusta-ui.png
  :width: 600
  :align: center

6. Finally, click "Save contact point" to complete the Robusta integration.


Configure Querying and Silencing
=================================================

To configure metrics querying and creating silences, add the following to ``generated_values.yaml`` and :ref:`update Robusta <Simple Upgrade>`.

.. code-block:: yaml

    globalConfig: # this line should already exist
        # add the lines below
        alertmanager_url: "https://alertmanager<url>.grafana.net"
        grafana_url: "https://<grafana url>.grafana.net"

        prometheus_url: "https://prometheus<url>.grafana.net/api/prom"

        # Create alert silencing when using Grafana alerts (optional)
        grafana_api_key: <YOUR GRAFANA EDITOR API KEY>
        alertmanager_flavor: grafana # (1)

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
