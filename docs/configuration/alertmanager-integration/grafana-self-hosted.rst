Grafana - Self-Hosted
*********************

Grafana can send alerts to the Robusta timeline for visualization and AI investigation.

.. image:: /images/grafana-docs-robusta-ui.png
  :width: 600
  :align: center

.. note::

    **Using Grafana Cloud?** See the :doc:`Grafana Cloud <grafana-cloud>` guide.

Option 1: Send Alerts to Robusta's Timeline
===========================================

Send Grafana alerts to Robusta's Timeline for visualization and AI investigation.

To configure it:

1. Get your Robusta ``account_id`` from your ``generated_values.yaml`` file. It appears under the ``globalConfig`` section.

2. Create an ``api key``

In the Robusta UI, navigate to the ``settings`` page, and select the ``API Keys`` tab.

.. image:: /images/robusta-api-keys.png
  :width: 600
  :align: center


Click ``New API Key``. Select a name for your key, and check the ``Alerts Write`` capability.
Generate and save your new ``API Key``

.. image:: /images/new-api-key.png
  :width: 600
  :align: center


3. In the Grafana UI, navigate to the ``Alerting`` tab, click on ``Manage Contact Points``, and then ``Create contact point``.

Select ``Webhook`` from the Integration options.
Add the following URL. Add your ``account_id`` to it:

.. code-block::

    https://api.robusta.dev/integrations/alerts/grafana?account_id=YOUR_ACCOUNT_ID

.. image:: /images/robusta-contact-point-1.png
  :width: 600
  :align: center

On the ``Optional Webhook settings`` add your ``API Key`` in the ``Bearer Token`` field:

.. image:: /images/robusta-contact-point-2.png
  :width: 600
  :align: center

Lastly, on the ``Notification settings``, check the ``Send resolved`` checkbox:

.. image:: /images/grafana-send-resolved.png
  :width: 600
  :align: center

Click  the ``Test`` button. If successful, you will receive a notification in the Robusta UI under the ``external`` cluster.

Save your new ``Contact Point``

4. Create a new ``Notification Policy``. Navigate to ``Alerting`` tab, and click ``Manage notification policies``
Create a new policy.

Add a policy without matchers, that handles all alerts. Disable grouping, by specifying ``Group By = ...``

.. image:: /images/robusta-new-notification-policy.png
  :width: 600
  :align: center


Save your new ``Notification Policy``


That's it!

You can now see your Grafana alerts in the Robusta Timeline, and use AI to analyze it.

Correlating Alerts with Kubernetes Resources
----------------------------------------------

To enable Robusta to correlate your Grafana alerts with the specific Kubernetes resources they're related to (pods, deployments, etc.), make sure the ``cluster`` label in your alerts matches ``clusterName`` in Robusta's ``generated_values.yaml``.

.. note::

    This is only required for Kubernetes alerts. You can send any alert to the Robusta timeline, including non-Kubernetes alerts.

Option 2: Inline Alert Enrichment and Routing
===========================================

Use Robusta to enrich alerts inline with extra context and route them to :doc:`other systems </configuration/sinks/index>` (Slack, Microsoft Teams, etc.). Learn more about :doc:`alert routing </notification-routing/index>`.

This is an alternative to Option 1, where alerts are only sent to Robusta's Timeline without inline enrichment or routing to other destinations.

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

5. Click "Test" button. Select "custom" and add a ``cluster_name`` or ``cluster`` label to send a test alert (Robusta requires that every alert have the ``cluster_name`` or ``cluster`` label).

.. image:: /images/grafana-alertmanager-test.png
  :width: 600
  :align: center

If successful, you will receive a notification in the Robusta UI, Slack or any other destination configured in Robusta, such as Microsoft Teams.

.. image:: /images/grafana-alertmanager-robusta-ui.png
  :width: 600
  :align: center

6. Finally, click "Save contact point" to complete the Robusta integration.
