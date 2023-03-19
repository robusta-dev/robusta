
Overview
================================

What is Robusta
^^^^^^^^^^^^^^^^^^^

The core of Robusta is a rules-engine. It listens for incoming events like Prometheus alerts and
CrashLoopBackOffs. Then it gathers observability data and remediates problems - all according to the rules.

We'll explain what that means, but first lets see an example.

Example - Better Prometheus Alerts
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``KubePodCrashLooping`` is a common Prometheus alert that identifies crashing pods. The Prometheus alert makes it clear
there is a problem, but it can't tell you *why* the pod is crashing.

Lets fix that with Robusta:

.. grid:: 2
    :margin: 0
    :padding: 0

    .. grid-item::
       :columns: 7

       .. code-block:: yaml

            - triggers:
              - on_prometheus_alert:
                  alert_name: KubePodCrashLooping
              actions:
              - logs_enricher: {}
              - pod_events_enricher: {}
              sinks:
              - slack_sink

       .. code-annotations::
            1. This rule will fire on the Prometheus alert named "KubePodCrashLooping"
            2. Robusta will find the pod that crashed and fetch logs
            3. The alert - along with data Robusta gathered - will be sent to Slack

    .. grid-item::
        :columns: 5

        To the left is a Robusta rule, or "playbook". It has three sections.

        **Triggers**: what events should cause this rule to run?

        **Actions**: what should happen when this rule runs?

        **Sinks**: where should results from this rule be sent?

Result
------------
.. image:: /images/example-alert.png
    :width: 800px

Benefits
^^^^^^^^^^^^
Robusta's main benefit is *obvious* and *actionable* alerts. But there are additional advantages:

1. **Efficient Logging:** When incidents occur at night, Robusta gathers the data you need and commits it to persistent storage for later investigation. This lets you ship far fewer logs, while making it easier to find the ones that matter.
2. **Developer Enablement:** Not all engineers have access to production, but with Robusta they can resolve issues anyway. Right from Slack.
3. **Knowledge Sharing:** Goodbye outdated runbook wikis. Hello awesome Slack messages you'll actually look at.

Common Questions
^^^^^^^^^^^^^^^^^^

How does Robusta know which pods are related to an alert?
-------------------------------------------------------------------------

Most Prometheus alerts have metadata like ``pod=<pod_name>``. Robusta reads this metadata and builds a map of where the
alert fired and on what resource.

Do I need to write my own rules to use Robusta?
---------------------------------------------------------------
No. Our community has already contributed rules for common Prometheus alerts. We have excellent coverage today and it
will only improve over time.


What events can Robusta listen to?
----------------------------------

Robusta can respond to any webhook or APIServer event. This includes:

* Prometheus Alerts
* Failed Jobs and CrashLoopBackOffs
* Change to Deployments

You can also forward custom events by webhook.

Actions Robusta can take
--------------------------

Robusta acts on incoming events. Actions are typically one of the following:

* **Enrich** - fetch extra data so you can see *why* the event occurred, then notify the user

  For example, given a Prometheus alert on CrashLoopBackOff, fetch Pod logs

* **Silence** - silence false positives based on rules you or the community define

  For example, Robusta has optional rules out of the box to silence APIServerDown alerts on GKE autopilot, where the alert constantly fires and is a false positive

* **Remediate** - automatically fix the problem, or "click to fix"

  For example, if the HPA reaches the max replica count then you can bump it up by 30% with the click of a button.

External Notifications
-------------------------

Robusta can notify in over XYZ external destinations, which we Robusta calls *sinks*. Builtin sinks include:

* Slack, MSTeams, Discord, Telegram
* PagerDuty and OpsGenie
* DataDog and the Robusta SaaS

...and many more.


Rules are pipelines
---------------------------

All events coming into Robusta are matched against ``triggers``.

Any matching events then flow to ``actions``.

Finally, any output from ``actions`` is sent to ``sinks``.

Every event in the pipeline has a type
------------------------------------------------

Each trigger outputs an event of a specific type. Each actions expects an event of a specific type.

For example, ``on_prometheus_alert`` outputs a ``PrometheusAlert`` event. Likewise, ``on_pod_update`` outputs a
``PodChangeEvent``.

These events flow into the ``actions`` section. Each ``action`` requires events of a specific type.
For example, the ``logs_enricher`` action expects to receive events that have a Pod object. This can be a
``PrometheusAlert`` event or a ``PodEvent``.
