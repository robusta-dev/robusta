Remediate using Kubernetes Job
============================================================

Robusta can run a Kuberntes Job to remediate any Prometheus Alert. In this example we'll remediate a Prometheus alert named ``TestAlert`` by running a Kubernetes job in response.


Implementation
****************

Add the following to your Helm values, under the :ref:`customPlaybooks<customPlaybooks>` value:

.. code-block:: yaml

    customPlaybooks:
    - triggers:
        # this trigger section defines when to run the remediation
        - on_prometheus_alert:
            alert_name: TestAlert
    
      actions:
        # this actions section defines what to do when the trigger fires
        - alert_handling_job:
            command:
              - sh
              - -c
              - echo "placeholder for taking an action that fixes the alert"
            image: busybox
            notify: true
            wait_for_completion: true
            completion_timeout: 100

Then, apply the Helm values with a :ref:`Helm Upgrade <Simple Upgrade>`.

Testing
**************

Trigger the newly added playbook by simulating a Prometheus alert.

.. code-block:: bash

    robusta playbooks trigger prometheus_alert alert_name=TestAlert