Opsgenie
##########

Robusta can report issues and events in your Kubernetes cluster to the OpsGenie alerts API.

To configure OpsGenie, We need an OpsGenie API key. It can be configured using the OpsGenie team integration.

Customizing Opsgenie Extra Details
------------------------------------------------

We can add Prometheus alert labels into Opsgenie alert extra details by setting `extra_details_labels` to `true` in the `sinksConfig` section.


Configuring the OpsGenie sink
------------------------------------------------

The OpsGenie sink supports static and dynamic team routing, optional fallback teams, tagging, and enrichment with Kubernetes labels.

.. admonition:: Add this to your `generated_values.yaml`

    .. code-block:: yaml

        sinksConfig:
        - opsgenie_sink:
            name: ops_genie_sink
            api_key: OpsGenie integration API key  # configured from OpsGenie team integration
            teams:
            - "noc"                  # Static team
            - "$labels.team"         # Dynamic team routing based on alert label
            default_team: "oncall"   # Optional fallback team for Dynamic team routing
            tags:
            - "prod a"
            extra_details_labels: false # optional, default is false

In this example:

- Alerts will be routed to the **"noc"** team by default.
- If the alert includes a **"team" label**, it will also be routed to the value of that label.
- If the **"team" label is missing**, the alert will be routed to the **"oncall"** team as a fallback.
- The tag **"prod a"** will be included with every alert.
- Kubernetes labels **will not be added** to alert details, as `extra_details_labels` is set to `false`.

.. note::

   - Dynamic team routing using label-based templates (e.g., ``$labels.team``) is only supported on **OpsGenie Standard** or **Enterprise** plans.
     If you are on a Free or Essentials plan, these templates will not function as expected.

   - The API key must be from a **Global API Integration** for dynamic routing to work.
     If you use a **team-specific API key**, alerts will be routed **only to that team**.

Save the file and apply the configuration:

.. code-block:: bash
   :name: cb-add-opsgenie-sink

    helm upgrade robusta robusta/robusta --values=generated_values.yaml

**Example Output:**

.. admonition:: Typically you'll send alerts from Robusta to OpsGenie and not deployment changes. We're showing a non-typical example with deployment changes because it helps compare the format with other sinks.

    .. image:: /images/deployment-babysitter-opsgenie.png
      :width: 1000
      :align: center


Action to connect Slack to OpsGenie
------------------------------------------------

The `opsgenie_slack_enricher` action enriches Slack alerts with OpsGenie integration. It performs the following:

- Adds a button in Slack to acknowledge the OpsGenie alert directly.
- Includes a link in Slack messages that redirects to the alert in OpsGenie for easy access.

To use this action, ensure it is included in your playbook configuration.

**Example Configuration:**

.. code-block:: yaml

   customPlaybooks:
   - actions:
     - opsgenie_slack_enricher:
         url_base: team-name.app.eu.opsgenie.com
     triggers:
     - on_prometheus_alert: {}

With this integration, teams can efficiently manage OpsGenie alerts directly from Slack.
