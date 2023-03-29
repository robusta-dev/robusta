
What is Robusta
================================

The core of Robusta is a rules-engine. Using predefined YAML instructions, it:

1. Listens to Kubernetes events, Prometheus alerts, and other sources
2. Gathers observability data - e.g. logs, graphs, thread dumps
3. Notifies in various destinations (optional)

Lets see two examples and how they're implemented with Robusta:

* :ref:`Automatically investigate a Prometheus alert`
* :ref:`Track failing Kubernetes Jobs`

Examples
^^^^^^^^^^^^^

Automatically investigate a Prometheus alert
----------------------------------------------

``KubePodCrashLooping`` is a Prometheus alert that identifies crashing pods. Here's what it normally looks like in Slack:

.. image:: /images/prometheus-alert-without-robusta.png
    :width: 800px

Clearly a pod is crashing in the cluster. But why?

With Robusta, the same Slack alert becomes this:

.. image:: /images/prometheus-alert-with-robusta.png
    :width: 800px

👆️ The Prometheus alert now contains pod logs. It also gained rapid-response buttons like "Investigate" and "Silence".

This looks like magic, but with Robusta it's actually 7 lines of YAML:

.. code-block:: yaml

    - triggers:
      - on_prometheus_alert:
          alert_name: KubePodCrashLooping
      actions:
      - logs_enricher: {}
      sinks:
      - slack_sink

**Note:** Robusta works out of the box, even without custom YAML! There are builtin rules from the community.

.. admonition:: How does Robusta know which pod to fetch logs from?

    In the above example:

    1. ``on_prometheus_alert`` receives an alert and parses the metadata, including the ``pod`` label.
    2. Robusta finds the relevant Kubernetes pod.
    3. ``logs_enricher`` receives the pod as input.

    Rules define logic and Robusta handles the plumbing.

Track failing Kubernetes Jobs
----------------------------------------

Instead of improving Prometheus alerts, Robusta can generate alerts itself. Robusta has builtin triggers for Kubernetes errors and change.

Lets send send a Slack notification when a Kubernetes Job fails:

.. code-block:: yaml

    - triggers:
      - on_job_failure: {}
      actions:
      - create_finding:
          title: "Job Failed"
          aggregation_key: "job_failure"
      - job_info_enricher: {}
      - job_events_enricher: {}
      - job_pod_enricher: {}

Here is the result:

.. image:: /images/on_job_failed_example.png
    :width: 800px

.. admonition:: Should I generate alerts with Robusta or with Prometheus?

    Robusta can respond to Prometheus alerts, or it can generate alerts itself.

    Most people mix and match the two options, depending on their use case. Here are some guidelines:

    * When alerts involve thresholds and time-series, use Prometheus. (Example: Job running > 18 hours.)
    * When alerts involve discrete events, use Robusta. (Example: Job failed.)

    That said, the choice is yours! Robusta is flexible and supports both approaches.

In the above example, the triggering condition was a failed Job.

Then Robusta generated a notification using four actions:

1. ``create_finding`` - create a notification
2. ``job_info_enricher`` - fetch the Job's status
3. ``job_events_enricher`` run ``kubectl get events`` and extract events related to this Job
4. ``job_pod_enricher`` find the latest Pod in this Job and fetch it's information

Next Steps
^^^^^^^^^^^^^

* See all the options for defining rules
* See example rules
* Install Robusta with Helm
