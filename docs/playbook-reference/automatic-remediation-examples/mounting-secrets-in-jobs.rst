Mount Sensitve Values in Remediation Jobs
==================================================

Sometimes you might want to reference sensite values like API keys in your remediation jobs. In such cases, Robusta lets you add them as a Kuberntes secret and reference them as environment variables.

Implementation
****************

Let's see how to mount a Kubernetes secret, that can be used in the remediation command:

.. code-block:: yaml

    customPlaybooks:
    - triggers:
        - on_prometheus_alert:
            alert_name: TestAlert
      actions:
        - alert_handling_job:
            # you can access mounted secrets here from the alert using environment variables
            command:
              - sh
              - -c
              - echo \"$GITHUB_SECRET\"
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

