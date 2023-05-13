Privacy and Security
############################

Robusta was designed with security in mind. Our four guiding security principles are:

1. **Less is more:** Don't send mountains of observability data when small subsets of the *right* data will do.
2. **Secure by default, configurable if necessary:** Do the right thing for most companies by default. Make it easy for companies with stricter needs to lock-down Robusta further or run it on-prem.
3. **Design for security:** Secure systems are designed to be secure from day one. Discuss security when planning new features.
4. **Experience matters:** Hire engineers who have built secure enterprise platforms before. Make security a core part of company culture.

Data Privacy
********************
The Robusta Open Source doesn't store persistent information itself.
Information is sent to destinations (sinks) like Slack or MSTeams, and they are responsible for storing it.

By default, the following data is sent to sinks. It can be customized if necessary.

- Prometheus alerts
- Alert enrichments, or insights. (Example: an alert for high memory usage will include a memory graph.)
- Technical events from Kubernetes itself. (Example: notifications on crashing pods, K8s warning events.)
- Logs from unhealthy pods. (Note: Robusta does *not* gather logs continuously, rather only from crashing or misbehaving pods.)

SaaS UI
----------
When the Robusta SaaS platform is enabled (optional), it receives the above data, as well as metadata about nodes and workloads in your cluster.
This is used, for example, to show you when deployments were updated and what YAML fields changed.

All data in the SaaS platform is encrypted at rest and stored in accordance with industry standards.

If necessary, the SaaS UI can be run on-prem as part of our paid plans. Contact support@robusta.dev for details.

Censoring Sensitive Data
*************************

Pod logs gathered by Robusta can be censored using regexes. Refer to the :ref:`Censoring Logs` guide for details.


Kubernetes Secrets
--------------------

If you'd like to monitor Helm releases with Robusta, access to Kubernetes Secrets is required. You can disable this feature and remove Robusta's access to Kubernetes secrets by setting ``monitorHelmReleases: false``
