Sinks
======

Playbooks results (findings) can be sent to one or more sinks (destinations). Findings will be automatically formatted in a way
that makes sense for each sink.

Supported sinks
^^^^^^^^^^^^^^^^^^^^^
The following sinks are supported:

* :ref:`Slack` - send playbooks results to a Slack channel
* :ref:`Robusta UI` - send playbooks results to Robusta's web UI
* :ref:`MS Teams` - send playbooks results to an MS Teams channel webhook.
* :ref:`Kafka` - send playbooks results to a Kafka topic
* :ref:`DataDog` - send playbooks results to the Datadog events API
* :ref:`OpsGenie` - send playbooks results to the OpsGenie alerts API
* :ref:`Telegram` - send playbooks results to Telegram group or private conversation
* :ref:`Webhook` - send playbooks results to a webhook
* :ref:`VictorOps` - send playbooks results to the VictorOps alerts API
* :ref:`PagerDuty` - send playbooks results to the PagerDuty alerts API
* :ref:`Discord` - send playbooks results to the Discord using webhook
* :ref:`Jira` - send playbooks results to the Jira
* :ref:`Mattermost` - send playbooks results to the Mattermost using webhook
* :ref:`Webex` - send playbooks results to the Webex using webhook
* :ref:`File` - send playbooks results to a file or console

**Need support for something not listed here?** `Tell us and we'll add it to the code. <https://github.com/robusta-dev/robusta/issues/new?assignees=&labels=&template=feature_request.md&title=New%20Sink:>`_

See :ref:`Defining additional sinks` for more details

Sending Findings to Specific Sinks
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
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

.. toctree::
   :hidden:
   :maxdepth: 1

   slack
   RobustaUI
   telegram
   discord
   kafka
   jira
   DataDog
   ms-teams
   mattermost
   webhook
   webex
   Opsgenie
   VictorOps
   PagerDuty
   file
