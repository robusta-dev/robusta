Route Alerts
===============

A sink can be configured to receive only certain findings. For example, you can send notifications to different Slack channels depending on the namespace:

.. code-block:: yaml

    sinksConfig:
    - slack_sink:
        name: slack_app_sink
        slack_channel: app-notifications
        api_key: secret-key
        match:
          namespace:
          - app
    - slack_sink:
        name: slack_system_sink
        slack_channel: system-notifications
        api_key: secret-key
        match:
          namespace:
          - kube-system


See :ref:`Sink matchers` for more details.

Default sinks
^^^^^^^^^^^^^^^^^^
If a playbook doesn't specify a sink then output will be sent to the default sinks. A sink is considered default
if it has the field `default: true` in the YAML.


You can define *NOT* rules by using regexes negative-lookahead regexes:

.. code-block:: yaml

    sinksConfig:
    - slack_sink:
        name: other_slack_sink
        slack_channel: pod-notifications
        api_key: secret-key
        match:
          # match all notifications EXCEPT for those related to pods and deployments
          # this uses negative-lookahead regexes as well as a regex OR
          kind: ^(?!(pod)|(deployment))
   - slack_sink:
        name: crashloopbackoff_slack_sink
        slack_channel: crash-notifications
        api_key: secret-key
        match:
          # match notifications related to crashing pods
          identifier: report_crash_loop
