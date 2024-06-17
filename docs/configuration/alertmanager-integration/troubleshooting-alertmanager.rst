Integrating AlertManager with the UI
*************************************************

Why Send Your Alerts to Robusta?
---------------------------------------

Benefits include:

* Persistent alert history on a filterable timeline
* Centralized view of alerts from all sources and AlertManager instances
* AI investigation of alerts
* Correlations between alerts and Kubernetes deploys
* and more!

.. image:: /images/robusta-ui-timeline.png
   :alt: Prometheus Alert History

How to Send Your Alerts To Robusta
---------------------------------------

Choose one of the following options:

1. :ref:`Enable Robusta's embedded kube-prometheus-stack stack <Embedded Prometheus Stack>`
2. :ref:`Add a webhook to your existing AlertManager (or equivalent integration) <alertmanager-setup-options>`.

Troubleshooting the embedded kube-prometheus-stack
-----------------------------------------------------

1. Did you install Robusta in the last 10 minutes? If so, wait 10 minutes and see if the problem resolves on its own.
2. Check if all Prometheus and AlertManager related pods are running and healthy
3. If you see OOMKills, increase the memory limits for the relevant pods.
4. If you are still having trouble, please reach out on our `Slack community <https://bit.ly/robusta-slack>`_.

Troubleshooting an external AlertManager webhook
-------------------------------------------------------

1. Are there errors in your AlertManager logs?
2. Are there errors in the Prometheus Operator logs (if relevant)?
3. Is Robusta the first receiver in your AlertManager configuration? If not, are all previous receivers configured with ``continue: true``?
4. If you are still having trouble, please reach out on our `Slack community <https://bit.ly/robusta-slack>`_.
