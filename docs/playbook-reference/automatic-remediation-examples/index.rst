:hide-toc:

Automatic Remediation
===============================

Robusta can automatically remediate Prometheus Alerts by running Kubernetes Jobs, or by running bash commands on existing nodes or pods.

By automatically remediating alerts you can, 

* Delete stuck Kubernetes resources like pods and jobs to keep your clusters healthy.
* Run Bash commands to gather information about your applications for faster issue resolution.

Get started: 

.. toctree::
   :maxdepth: 1

   job-to-remediate-alert
   mounting-secrets-in-jobs
   alert-metadata-in-job
   bash-command-to-remediate-alert



Further Reading
*****************

* Reference for the :ref:`alert_handling_job<alert_handling_job>` action
* Reference for the :ref:`node_bash_enricher<node_bash_enricher>` action
* :ref:`More remediation actions <Remediation>`

