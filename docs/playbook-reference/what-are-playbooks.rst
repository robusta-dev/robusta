.. _how-it-works-index:

What are Playbooks?
=================================================

The `Robusta Open Source <https://github.com/robusta-dev/robusta>`_ is a rules-engine for Kubernetes, designed for monitoring and observability use cases.

In Robusta, rules are called *playbooks*. Every playbook consists of a *trigger* (e.g. a Crashing Pod, a Prometheus Alert, or some other condition) and one or
more *actions*. Actions can enrich alerts, silence them, or remediate problems.

Conceptually, Robusta does three things:

1. **Listens passively to various sources:** Robusta monitors Kubernetes events, Prometheus alerts, and other sources to stay informed about your cluster's current state.
2. **Actively collects observability data:** When noteworthy events occur, Robusta actively gathers and correlates information such as logs, graphs, and thread dumps. All according to the playbooks defined in Robusta.
3. **Sends notifications:** Based on your preferences, Robusta notifies in :ref:`sinks <Sinks Reference>` like Slack, MSTeams, and PagerDuty

To get a feel for playbooks, let's explore two examples:

* :ref:`Automatically Investigate a Prometheus Alert` *(Prometheus required)*
* :ref:`Track Failing Kubernetes Jobs` *(No Prometheus required)*

Example Playbooks
^^^^^^^^^^^^^^^^^^^^^^

Automatically Investigate a Prometheus Alert
----------------------------------------------

``KubePodCrashLooping`` is a Prometheus alert that identifies crashing pods. It normally looks like this in Slack:

.. image:: /images/prometheus-alert-without-robusta.png
    :width: 800px

While it's clear that a pod is crashing in the cluster, it's not obvious why. With Robusta, the same Slack alert is transformed into this:

.. image:: /images/prometheus-alert-with-robusta.png
    :width: 800px

Now the alert contains pod logs and rapid-response buttons like "Investigate" and "Silence".

This enhancement is implemented with 5 lines of YAML in Robusta:

.. code-block:: yaml

    - triggers:
      - on_prometheus_alert:
          alert_name: KubePodCrashLooping
      actions:
      - logs_enricher: {}

Here's how it works:

1. A Prometheus alert fires and is sent to Robusta by webhook
2. Robusta evaluates all of the ``on_prometheus_alert`` triggers that are currently loaded.
3. If the alert name is ``KubePodCrashLooping``, there's a match and Robusta runs the above playbook.
4. The Prometheus alert is mapped to a Kubernetes resources (in this case a Pod) using the alert's metadata.
5. All actions in the playbook execute - in this case, a single action called ``logs_enricher``.
6. ``logs_enricher`` is a builtin action that takes a Pod-related event as input and fetch logs. It also builds a notification message.
7. The notification is sent to sinks according to global settings.

.. admonition:: Do I need to write playbooks to use Robusta?

    Nope, you can get started without writing any YAML. Robusta includes builtin playbooks covering dozens of problems seen on real-world clusters.

Track Failing Kubernetes Jobs
----------------------------------------

Robusta can generate alerts by listening to the APIServer, rather than just improving existing Prometheus alerts.

This is useful if you don't have Prometheus, and for cases when writing Prometheus alerts is awkward.

Lets notify in Slack when a Kubernetes Job fails:

.. image:: /images/on_job_failed_example.png
    :width: 800px

Here is the Robusta rule that generates this notification:

.. code-block:: yaml

    - triggers:
      - on_job_failure: {}
      actions:
      - create_finding:
          title: "Job Failed"
          aggregation_key: "JobFailure"
      - job_info_enricher: {}
      - job_events_enricher: {}
      - job_pod_enricher: {}

In this example, the trigger was ``on_job_failure``. Robusta generated a notification using four actions:

1. ``create_finding`` - create the notification message itself
2. ``job_info_enricher`` - fetch the Job's status and attach it
3. ``job_events_enricher`` run ``kubectl get events`` and attach events related to this Job
4. ``job_pod_enricher`` find the latest Pod in this Job and attach its information

.. _robusta-or-prometheus-alerts:

.. admonition:: Should I generate alerts with Robusta or with Prometheus?

    Robusta can respond to Prometheus alerts, or it can generate alerts itself. Most users mix and match these options, depending on their use case. Here are some guidelines:

    * Use Prometheus for alerts involving thresholds and time-series (e.g. Jobs running over 18 hours).
    * Use Robusta for alerts involving discrete events (e.g. Jobs failing).

    That said, the choice is yours. Robusta is flexible and supports both approaches.

Next Steps
^^^^^^^^^^^^^

* :ref:`See reference guide on defining playbooks <defining-playbooks>`
* :ref:`Install Robusta with Helm <install>`