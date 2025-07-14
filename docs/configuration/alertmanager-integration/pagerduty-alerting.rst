PagerDuty Integration
****************************************

PagerDuty can send both incidents and full alert-level data to Robusta for enrichment and resolution tracking.

This guide explains how to set up both integrations, and how to forward alerts from sources like Alertmanager using PagerDuty AIOps Event Orchestration.

After completing this tutorial, we recommend confirming that findings appear correctly in the Robusta UI timeline.

Prerequisite
=================================
* A Robusta account with API access.
* For alert-level forwarding: an AIOps-enabled PagerDuty plan.
* A Robusta cluster name, as defined in your ``generated_values.yaml``.

Send Incidents to Robusta
============================

To send PagerDuty incidents (triggered/resolved) to Robusta:

Step 1: Create a Robusta API Key
---------------------------------
1. In the Robusta UI, navigate to **Settings → API Keys**.
2. Click **New API Key**.
3. Name the key ``PagerDuty``, grant it ``Read/Write`` access to alerts, then click **Generate API Key**.
4. Copy and securely save the generated API key.

Step 2: Get Your Account ID
-------------------------------
1. From your Robusta ``generated_values.yaml`` file, locate and copy the ``account_id``.
   It will look like:

.. code-block::

    account_id: caa68d87-XXXX-XXXX-XXXX-a6514ccb11eb

Step 3: Create a Webhook in PagerDuty
-------------------------------------------
1. In PagerDuty, go to **Integrations → Generic Webhooks v3**.
2. Click **New Webhook**.

Step 4: Configure the Webhook
----------------------------------------
Set the following values:

* **Webhook URL**:

.. code-block::

    https://api.robusta.dev/integrations/generic/pagerduty/incidents

* **Custom Headers**:

.. code-block::

    account-id: <your_account_id>
    Authorization: Bearer <ROBUSTA_API_KEY>

Replace the placeholders with values from Step 1 and Step 2.

Once configured, PagerDuty will begin sending incident-level data to Robusta. These will appear in the Robusta UI timeline.

Send Alerts to Robusta (AIOps Plans Only)
==============================================

For Robusta AIOps users, you can send full alert-level data in addition to incidents.

Step 1: Go to AIOps → Event Orchestration
----------------------------------------------
1. In PagerDuty, go to **AIOps → Event Orchestration**.
2. Click **New Orchestration** and name it ``Robusta``.

Forwarding Alerts via Event Orchestration
----------------------------------------------

**Recommended for Alertmanager Users**

If you already use PagerDuty Event Orchestration to forward alerts from systems like Alertmanager, we recommend forwarding those alerts **directly to Robusta**.

Why this matters
~~~~~~~~~~~~~~~~
Robusta’s AIOps integration works best when it receives structured alert data directly. Routing alerts through intermediate services or limited integrations may strip important context.

Step 1: Create an Integration for Alertmanager
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
1. In Event Orchestration, create a new **Integration** named ``Alertmanager``.
2. Use the following webhook URL:

.. code-block::

    https://api.robusta.dev/integrations/generic/pagerduty/alerts

Step 2: Configure a Service Route
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
1. At the end of your orchestration rule chain, add a **Service Route**.
2. Route events with the source ``Alertmanager`` to the ``Robusta`` webhook.

This ensures full alert payloads are delivered directly to Robusta.

Step 2: Add a New Rule
----------------------------
1. Under your ``Robusta`` orchestration, add a new rule.
2. For **"When this rule is applied"**, select **Always, for all events**.
3. Click **Next**.

Step 3: Add a Webhook Action
-------------------------------
1. Under **Automation → Webhook Actions**, enable:
   ``Use webhooks if an event reaches this rule``.

2. Configure the webhook as follows:

* **Name**: ``Robusta``

* **URL**:

.. code-block::

    https://api.robusta.dev/integrations/generic/pagerduty/alerts

* **Headers**:

.. code-block::

    account-id: <your_account_id>
    Authorization: Bearer <ROBUSTA_API_KEY>

* **Body (key-value pairs)**:

.. code-block:: json

    {
      "custom_details": "{{event.custom_details}}",
      "summary": "{{event.summary}}",
      "source": "{{event.source}}",
      "dedup_key": "{{event.dedup_key}}",
      "severity": "{{event.severity}}"
    }

3. Click **Save**.

Step 4: Route Matching
---------------------------
In the routing configuration, route it to the the service of your choice or you can do it dynamically by setting the route to:

.. code-block::

    event.source

Using this regular expression:

.. code-block::

    .*

This ensures all alert sources are routed properly to their Pagerduty Services.

Verify it Works
=============================

To confirm the integration:

* Trigger an alert from Alertmanager, Nagios, or another connected system.
* Check that the alert appears in the Robusta UI timeline under the correct cluster.
* Confirm the incident is routed to the correct Service in Pagerduty.

Optional: Cluster Name via Query Param
============================================

You can specify the target cluster using a query parameter in the webhook URL:

.. code-block::

    https://api.robusta.dev/integrations/generic/pagerduty/incidents?cluster=your-cluster-name

This is useful for multi-cluster setups where Robusta should assign findings to a specific cluster.

For example:

.. code-block::

    https://api.robusta.dev/integrations/generic/pagerduty/incidents?cluster=roi-test-cluster

This will create findings in ``roi-test-cluster``.
