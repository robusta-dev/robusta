Dropping Specific Alerts
=============================

This guide defines a sink that receives all notifications *except* for a specific alert.

To drop a specific notification globally from *all sinks*, see :ref:`Silencing Alerts`.

Exclude Alerts by Alert Name
------------------------------------------------

Using :ref:`sink scopes <sink-scope-matching>`, you can drop all alerts with a specific name:

.. code-block:: yaml

    sinksConfig:
    - slack_sink:
        name: main_sink
        slack_channel: main-notifications
        api_key: secret-key
        - scope:
            exclude:
            # don't send notifications where the alert name is ANY of the following
            - identifier: [ImagePullBackoff, CrashLoopBackoff, CPUThrottlingHigh]


Exclude Alert by Namespace
------------------------------------------------

Using :ref:`sink scopes <sink-scope-matching>`, you can drop all alerts from a specific namespace:

.. code-block:: yaml

    sinksConfig:
    - slack_sink:
        name: other_slack_sink
        slack_channel: no-pods-or-deployments
        api_key: secret-key
        scope:
          exclude:
            - namespace: ["kube-system"]
