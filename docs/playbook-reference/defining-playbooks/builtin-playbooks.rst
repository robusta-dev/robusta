Builtin Playbooks
####################

Robusta includes builtin playbooks that:

* Enhance common Prometheus alerts
* Complement Prometheus with direct APIServer monitoring

You can view builtin playbooks in the default Helm values.

In this guide, we explain the default configuration.

Default Prometheus Enhancements
-----------------------------------

The following default playbook handles all Prometheus alerts that Robusta receives:

.. code-block:: yaml

   builtinPlaybooks:
   - triggers:
     - on_prometheus_alert: {}
     actions:
     - default_enricher: {}

There are additional enrichments for specific alerts. For example:

To define additional playbooks for your own alerts, refer to the :doc:`Custom Alert Enrichment </playbook-reference/prometheus-examples/index>` guide.

Default Prometheus Silencing
--------------------------------

Robusta uses *silencer* actions to flag false positive alerts and prevent them from being sent.

Silencers are just regular actions that call a special silencing API in their code.

To define your own silencers, refer to the playbook actions documentation.
