PagerDuty
##########

`PagerDuty <https://www.pagerduty.com/>`_ is a leading cloud incident response management tool. It integrates data from multiple monitoring systems into a single view.

`Robusta <https://docs.robusta.dev/master/index.html>`_ can send playbooks results to the PagerDuty alerts API.
Robusta supports two kinds of reporting:
 1. `Change Events <https://support.pagerduty.com/docs/change-events>`_
 2. `Alert <https://support.pagerduty.com/docs/alerts>`_

.. admonition:: To use Change Events or Alerts, you may need to set up the `Services <https://support.pagerduty.com/docs/services-and-integrations>`_.

   Once you have logged into the PagerDuty dashboard:

    - Navigate to `Service` > `New Service` (Top right)
    - Input `Name` and `Description` and Tap on the `Next` button
    - Choose `Generate a new Escalation Policy` or `Select an existing Escalation Policy` and Tap on next
    - On the next screen input the configuration details
    - On the `Integrations` screen check the `Events API V2` option and Tap on the `Create` button in the bottom on the screen
    - Copy the `Integration Key`. A sample key would look like: f6c6e02a5a1a490ee02e90cde19ee388


| To configure PagerDuty sink on Robusta, the Integration API Key (string) is needed.

Configuring the PagerDuty sink
------------------------------------------------

.. admonition:: Add this to your generated_values.yaml

    .. code-block:: yaml

        sinkConfig:
            - pagerduty_sink:
                name: main_pagerduty_sink
                api_key: <api key> # e.g. f653634653463678fadas43534506

        - actions:
          - resource_babysitter: {}
          sinks:
          - main_pagerduty_sink
          triggers:
          - on_deployment_all_changes: {}
          - on_daemonset_all_changes: {}
          - on_statefulset_all_changes: {}

Save the file and run

.. code-block:: bash
   :name: cb-add-pagerduty-sink

    helm upgrade robusta robusta/robusta --values=generated_values.yaml

**Example Output:**

.. admonition:: To view the Changed Events, on PagerDuty's dashboard navigate to `Incidents` > `Recent Changes`

    .. image:: /images/change-events-updated-deployment-pagerduty.png
      :width: 1000
      :align: center

.. admonition:: To view the Alerts, on PagerDuty's dashboard navigate to `Incidents` > `Alerts`

    .. image:: /images/alert-on-cpu-usage-spike-pagerduty.png
      :width: 1117
      :align: center

.. admonition:: View full incident log
    :class: important

    To view the full incident log, setup `Robusta UI sink <https://bit.ly/robusta-ui-pager-duty>`_.
