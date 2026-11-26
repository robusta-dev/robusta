Scans
########

Robusta runs a weekly KRR scan from a CronJob, see :ref:`krr-cronjob`.

.. warning::

    The ``krr_scan`` and ``popeye_scan`` actions are deprecated and no longer supported. A playbook that still uses one of them is loaded, and the runner logs an error instead of running the action. Remove them from your playbooks.
