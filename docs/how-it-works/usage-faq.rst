
Usage FAQ
==========

Does Robusta have builtin alerts?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Yes. Robusta includes built-in alerts based on Prometheus and direct APIServer monitoring.

These alerts work out of the box without any configuration.

You can also :ref:`write your own `.

What events can Robusta listen to?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Robusta listens to:

* Prometheus alerts
* CrashLoopBackOffs
* OOMKills
* Job Failures
* Other APIServer errors
* Updates to Kubernetes Deployments and other resources

Want Robusta to respond to a custom event? Just send your event to Robusta by webhook.

What actions can Robusta take?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Actions typically do one of the following:

* Correlate existing observability data
* Perform high-fidelity data collection (e.g. fetch heap dumps)
* Remediate problems
* Silence false alarms

For concrete examples, see :ref:`What is Robusta`.

Where can Robusta send notifications?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In Robusta, destinations are called *sinks*. Here are some built-in sinks:

* Chat apps: *Slack, MSTeams, Discord, and Telegram*
* Incident management tools: *PagerDuty and OpsGenie*
* Monitoring Platforms: *DataDog and the Robusta SaaS*

See the full list :ref:`here <Sinks>`.
