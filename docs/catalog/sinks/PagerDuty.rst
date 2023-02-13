PagerDuty
##########

`PagerDuty <https://www.pagerduty.com/>`_ is a popular incident response tool. Robusta is a popular Kubernetes monitoring solution, based on Prometheus.

`Robusta <https://docs.robusta.dev/master/index.html>`_ can send three types of data to the PagerDuty API:

*  `Change Events <https://support.pagerduty.com/docs/change-events>`_ - for example, when Deployments are updated

* Enriched Prometheus `alerts <https://support.pagerduty.com/docs/alerts>`_ - Robusta receives the alert from Prometheus, attaches context like Pod logs, and forward to PagerDuty

* Standalone `alerts <https://support.pagerduty.com/docs/alerts>`_ - if you don’t use Prometheus, Robusta can still send alerts to PagerDuty for errors like CrashLoopBackOff



Setting up Services
------------------------------

By default, Robusta sends notifications when Kubernetes pods crash.

1. To use Change Events or Alerts, you may need to set up the `Services <https://support.pagerduty.com/docs/services-and-integrations>`_

2. Login to your PagerDuty dashboard

3. Navigate to `Service` > `New Service` (Top right)

4. Input `Name` and `Description` and Tap on the `Next` button

5. Choose `Generate a new Escalation Policy` or `Select an existing Escalation Policy` and Tap on next

6. On the next screen input the configuration details

7. On the `Integrations` screen check the `Events API V2` option and Tap on the `Create` button in the bottom on the screen

8. Copy the `Integration Key`. A sample key would look like: f6c6e02a5a1a490ee02e90cde19ee388



Configuring the PagerDuty sink
------------------------------------------------
By default Robusta already listens to alerts and those will be sent to the `sink <https://docs.robusta.dev/master/catalog/sinks/index.html>`_ as soon as you add it.  With the default triggers Robusta also tracks changes to Deployments, DaemonSets and StatefulSets.

| To configure PagerDuty sink on Robusta, add this code to your `generated_values.yaml` file.


.. admonition:: PagerDuty API key
    :class: note

    To a generate the PagerDuty API key you will need to setup the services as mentioned above.

.. admonition:: generated_values.yaml

    .. code-block:: yaml

        sinksConfig:
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

Using the above example, Robusta will track changes to `Deployments`, `DaemonSets` & `StatefulSets` and sends those alerts to PagerDuty's events API v2. You can further see those Alerts or Changes in the PagerDuty portal.

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
