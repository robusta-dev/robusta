Refer Alert Metadata in Remediation Jobs
================================================

When remediating based on alerts, you can access all the alert metadata like name, namespace, cluster name, pod, node and more as environment variables.


Implementation
****************
In this example we are referencing the alert name and a label called region as environment variables in the remediation job. 


.. code-block:: yaml

    customPlaybooks:
    - triggers:
        - on_prometheus_alert:
            alert_name: TestAlert
      actions:
        - alert_handling_job:
            # you can access information from the alert using environment variables
            command:
              - sh
              - -c
              - echo \"$ALERT_NAME $ALERT_LABEL_REGION dumping all available environment variables, which include alert metadata and labels\" && env && sleep 60
            image: busybox
            notify: true
            wait_for_completion: true
            completion_timeout: 100
            env:
              - name: GITHUB_SECRET
                valueFrom:
                  secretKeyRef:
                    name: robusta-github-key
                    key: githubapikey

Then do a :ref:`Helm Upgrade <Simple Upgrade>`.

.. note::

    * Alert labels are added as environment variables in the following format ``ALERT_LABEL_{LABEL_NAME}``. For example a label named ``foo`` becomes ``ALERT_LABEL_FOO``

