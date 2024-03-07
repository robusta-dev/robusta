Remediate Prometheus Alerts
===============================

Robusta can respond to Prometheus alerts and automatically remediate them.

Using Kubernetes Jobs for Alert Remediation
***********************************************

A popular remediation method involves running Kubernetes Jobs when alerts fire.

Add the following to your :ref:`customPlaybooks<customPlaybooks>`:

.. code-block:: yaml

    customPlaybooks:
    # Change the following line according to your needs
    - triggers:
        - on_prometheus_alert:
            alert_name: TestAlert
      actions:
        - alert_handling_job:
            # you can access information from the alert by environment variables
            command:
              - sh
              - -c
              - "echo '$ALERT_NAME fired... Now dumping all available environment variables, which include alert metadata and labels' && env && sleep 60"
            image: busybox
            notify: true
            wait_for_completion: true
            completion_timeout: 100
            # you can also inject secrets from the Robusta pod itself into the remediation Job's Pod
            env_vars:
              - name: GITHUB_SECRET
                valueFrom:
                  secretKeyRef:
                    name: robusta-github-key
                    key: githubapikey

Perform a :ref:`Helm Upgrade <Simple Upgrade>`.

.. note::

    ``alert_name`` should be the exact name of the Prometheus Alert. For example, ``CrashLoopBackOff`` will not work, because the actual Prometheus Alert is ``KubePodCrashLooping``.

Test this playbook by simulating a Prometheus alert:

.. code-block:: bash

    robusta playbooks trigger prometheus_alert alert_name=TestAlert

Running Bash Commands for Alert Remediation
********************************************

Alerts can also be remediated with bash commands:

.. code-block:: yaml

    customPlaybooks:
    - triggers:
      - on_prometheus_alert:
          alert_name: SomeAlert
      actions:
      - node_bash_enricher:
        bash_command: do something

Further Reading
*****************

* Reference for the :ref:`alert_handling_job<alert_handling_job>` action
* Reference for the :ref:`node_bash_enricher<node_bash_enricher>` action
* :ref:`More remediation actions <Remediation>`

..     .. tab-item:: Remediate alerts

..         .. admonition:: Temporarily increase the HPA maximum so you can go back to sleep

..             .. image:: /images/alert_on_hpa_reached_limit1.png
..                 :width: 600
..                 :align: center
