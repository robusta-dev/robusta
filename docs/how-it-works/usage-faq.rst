
Usage FAQ
==========

Do I need to write my own rules?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
No. Our community has already contributed many rules. They work out of the box without any configuration.

That said, you can always write your own.

What events can Robusta listen to?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Robusta can respond to:

* Prometheus alerts
* APIServer events (CrashLoopBackOffs, OOMKills, and more)
* Changes to Kubernetes resources (updated deployments, new pods, etc)

You can also forward custom events by webhook.

What actions can Robusta take?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Actions typically do one of the following:

* Correlate existing observability data. For example, when a Pod is...

  * Pending, then ask the APIServer why it's pending
  * OOMKilled, then attach a graph of memory usage from Prometheus
  * in CrashLoopBackOff, then fetch Pod logs

* Collect high-fidelity observability data.

  * For example, when a Java application has a memory leak, run jmap on-demand

* Remediate problems

  * For example, if the HPA reaches the maximum scaling limit at 2AM, increase the limit by 30% from Slack. Fix it properly in the morning.

* Silence false alarms

  * For example, don't notify about APIServerDown on GKE autopilot clusters. It's a known false positive.

Where can Robusta send notifications?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In Robusta, destinations are called *sinks*. Here are some built-in sinks:

* Chat apps: *Slack, MSTeams, Discord, and Telegram*
* Incident management tools: *PagerDuty and OpsGenie*
* Monitoring Platforms: *DataDog and the Robusta SaaS*

See the full list :ref:`here <Sinks>`.
