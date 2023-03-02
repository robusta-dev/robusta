PagerDuty
##########

`PagerDuty <https://www.pagerduty.com/>`_ is a popular incident response tool.


`Robusta <https://docs.robusta.dev/master/index.html>`_ is a popular Open-Source Kubernetes monitoring tool that allows you to find major problems in your Cluster by tracking changes and identifying bad practices.

* With its awesome Prometheus integration, you can easily monitor and analyze your system's performance, set up alerts on crashing pods or unavailable replicas, and troubleshoot issues in real-time.
* Robusta provides comprehensive metrics and analytics that help you identify bottlenecks, optimize resource usage, and improve the overall health of your system.
* Its seamless integration with Prometheus makes it easy to monitor your system's performance and identify issues as soon as they arise.

| With Robusta, you can ensure that your system is running smoothly and efficiently, while avoiding common pitfalls and bad practices. Whether you're a developer, a sysadmin, or a DevOps engineer, Robusta can help you keep your cluster healthy and efficient.

Robusta can send three types of data to the PagerDuty API:

*  `Change Events <https://support.pagerduty.com/docs/change-events>`_ - for example, when Deployments are updated

* Enriched Prometheus `alerts <https://support.pagerduty.com/docs/alerts>`_ - Robusta receives the alert from Prometheus, attaches context like Pod logs, and forward to PagerDuty

* Standalone `alerts <https://support.pagerduty.com/docs/alerts>`_ - if you don’t use Prometheus, Robusta can still send alerts to PagerDuty for errors like CrashLoopBackOff



Prerequisites
------------------------------

You need an integration key for a PagerDuty service. Here is how to generate it.

1. Login to your PagerDuty dashboard

2. Navigate to `Service` > `New Service` (Top right)

3. Input `Name` and `Description` and Tap on the `Next` button

4. Choose `Generate a new Escalation Policy` or `Select an existing Escalation Policy` and Tap on next

5. On the next screen input the configuration details

6. On the `Integrations` screen check the `Events API V2` option and Tap on the `Create` button in the bottom on the screen

7. Copy the `Integration Key`. A sample key would look like: f6c6e02a5a1a490ee02e90cde19ee388



Configuring the PagerDuty sink
------------------------------------------------

**Sending Alerts to PagerDuty**

| To send alerts from Robusta to PagerDuty, add the following code to your generated_values.yaml file. This will send all alerts Robusta receives - whether they originate in Prometheus or in Robusta itself.

.. code-block:: yaml

  sinksConfig:
      - pagerduty_sink:
          name: main_pagerduty_sink
          api_key: <api key> # e.g. f653634653463678fadas43534506

Save the file and run

.. code-block:: bash
   :name: cb-add-pagerduty-sink

    helm upgrade robusta robusta/robusta --values=generated_values.yaml

Example Output:

.. admonition:: To view the Alerts, on PagerDuty's dashboard navigate to `Incidents` > `Alerts`

    .. image:: /images/alert-on-cpu-usage-spike-pagerduty.png
      :width: 1117
      :align: center

**Sending Kubernetes Changes to PagerDuty**

| To send Kubernetes changes from Robusta to PagerDuty, add the following code to your generated_values.yaml file. This will send all changes to PagerDuty, in addition to the alerts mentioned above.

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

Save the file and run

.. code-block:: bash
   :name: cb-add-pagerduty-sink

    helm upgrade robusta robusta/robusta --values=generated_values.yaml

Example Output:

.. admonition:: To view the Changed Events, on PagerDuty's dashboard navigate to `Incidents` > `Recent Changes`

    .. image:: /images/change-events-updated-deployment-pagerduty.png
      :width: 1000
      :align: center
