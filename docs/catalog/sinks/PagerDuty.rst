PagerDuty
##########

Robusta can send playbooks results to the PagerDuty alerts API.

| To configure PagerDuty, a PagerDuty Integration API Key (string) is needed.

Configuring the PagerDuty sink
------------------------------------------------

.. admonition:: Add this to your generated_values.yaml

    .. code-block:: yaml

        sinks_config:
            - pagerduty_sink:
                name: main_pagerduty_sink
                api_key: <api key> # e.g. f653634653463678fadas43534506
                
Save the file and run

.. code-block:: bash
   :name: add-msteams-sink

    helm upgrade robusta robusta/robusta --values=generated_values.yaml
**Example Output:**

.. admonition:: Typically you'll send alerts from Robusta to PagerDuty and not deployment changes. We're showing a non-typical example with deployment changes because it helps compare the format with other sinks.

    .. image:: /images/deployment-babysitter-pagerduty.png
      :width: 1000
      :align: center

.. admonition:: Alerts from Robusta to PagerDuty

    .. image:: /images/alert-on-crashing-pod-pagerduty.png
      :width: 1117
      :align: center