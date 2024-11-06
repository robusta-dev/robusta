
Usage FAQ
==========

Does Robusta have Builtin Alerts?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Yes. Robusta includes built-in alerts based on Prometheus and direct APIServer monitoring.

These alerts work out of the box without any configuration.

You can also :ref:`write your own Prometheus alerts <Create Custom Prometheus Alerts>`.

What Events Can Robusta Listen to?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Robusta listens to:

* Prometheus alerts
* CrashLoopBackOffs
* OOMKills
* Job Failures
* Other APIServer errors
* Updates to Kubernetes Deployments and other resources

See the full list in :ref:`All Triggers <Triggers Reference>`.

Want Robusta to respond to a custom event? Just send your event to Robusta by webhook.

What Actions Can Robusta Take?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Actions typically do one of the following:

* Correlate existing observability data
* Perform high-fidelity data collection (e.g. fetch heap dumps)
* Remediate problems
* Silence false alarms

See the full list in :ref:`All Actions <Actions Reference>`.

For examples, see :ref:`What are Playbooks?`.

Where Can Robusta Send Notifications?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In Robusta, destinations are called *sinks*. Here are some built-in sinks:

* Chat apps: *Slack, MSTeams, Discord, and Telegram*
* Incident management tools: *PagerDuty and OpsGenie*
* Monitoring Platforms: *DataDog and the Robusta SaaS*

See the full list in :ref:`Sinks Reference`.
