:hide-toc:

Kubernetes Change Tracking
==========================================

Robusta allows you to track and respond to Kubernetes changes.

You can use this to get notified about problems in your cluster without relying on Prometheus metrics and defining complex PromQL alerts.
Robusta listens to the API Server directly and triggers playbooks when changes occur.

Another use case is **automatic remediation** of Kubernetes problems - Refer to :ref:`Remediation` for more information.

.. toctree::
   :maxdepth: 1

   playbook-failed-liveness
   playbook-job-failure
   playbook-track-changes
   playbook-track-secrets
