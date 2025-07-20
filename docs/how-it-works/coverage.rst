Insights Coverage
####################################

Robusta's monitors these alerts and errors by default. It finds insights and suggests fixes.

.. warning::

    This page is under construction! Current contents are incomplete.

Prometheus Alerts
----------------------

* CPUThrottlingHigh - show the reason and how to fix it
* HostOomKillDetected - show which pods were killed
* KubeNodeNotReady - show node resources and effected pods
* HostHighCpuLoad - show CPU usage analysis
* KubernetesDaemonsetMisscheduled - flag known false positives and suggest fixes
* KubernetesDeploymentReplicasMismatch - show the deployment's status
* NodeFilesystemSpaceFillingUp - show disk usage

.. warning::

    You must :ref:`send your Prometheus alerts to Robusta by webhook <Integrating with Prometheus>` for these to work.

Other errors
----------------

These are identified by listening to the API Server:

* CrashLoopBackOff
* ImagePullBackOff
* Node NotReady

Additionally, all Kubernetes Events (``kubectl get events``) of WARNING level and above are sent to the Robusta UI.

Change Tracking
----------------

By default all changes to Deployments, DaemonSets, and StatefulSets are sent to the Robusta UI for correlation
with Prometheus alerts and other errors.

These changes are not sent to other sinks (e.g. Slack) by default because they are spammy. :ref:`Routing Cookbook`
explains how to selectively track changes you care about in Slack as well.

We also wrote a blog post `Why everyone should track Kubernetes changes and top four ways to do so <https://home.robusta.dev/blog/why-everyone-should-track-and-audit-kubernetes-changes-and-top-ways/>`_

Optional add-ons
---------------------------

These have the potential to be spammy so they aren't enabled by default.

We will enable them once we finish the fine-tuning. Until them, you can enable them yourself.

.. robusta-action:: playbooks.robusta_playbooks.autoscaler.alert_on_hpa_reached_limit


..
    these are all commented out for now - no point in showing how they're configured as it doesn't add anything
    this is an RST comment BTW as are the lines below
    .. robusta-action:: playbooks.robusta_playbooks.node_enrichments.node_health_watcher
    .. robusta-action:: playbooks.robusta_playbooks.restart_loop_reporter.restart_loop_reporter
    .. robusta-action:: playbooks.robusta_playbooks.cpu_throttling.cpu_throttling_analysis_enricher
    .. robusta-action:: playbooks.robusta_playbooks.image_pull_backoff_enricher.image_pull_backoff_reporter
    .. robusta-action:: playbooks.robusta_playbooks.oom_killer.oom_killer_enricher
    .. robusta-action:: playbooks.robusta_playbooks.daemonsets.daemonset_misscheduled_analysis_enricher
    .. robusta-action:: playbooks.robusta_playbooks.daemonsets.daemonset_misscheduled_smart_silencer
