Defining additional sinks
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Here is a full example showing how to configure all possible sinks:

.. code-block:: yaml

    sinksConfig:
    - slack_sink:
        name: main_slack_sink
        slack_channel: channel-name
        api_key: secret-key    # generated with `robusta integrations slack`
    - robusta_sink:
        name: robusta_ui_sink
        token: secret-api-key  # generated with `robusta gen-config`
    - ms_teams_sink:
        name: main_ms_teams_sink
        webhook_url: teams channel incoming webhook  # configured using teams channel connectors
    - kafka_sink:
        name: kafka_sink
        kafka_url: "localhost:9092"
        topic: "robusta-playbooks"
        default: false
    - datadog_sink:
        name: datadog_sink
        api_key: "datadog api key"
        default: false
    - opsgenie_sink:
        name: ops_genie_sink
        api_key: OpsGenie integration API key  # configured from OpsGenie team integration
        teams:
        - "noc"
        - "sre"
        tags:
        - "prod a"
    - telegram_sink:
        name: telegram_sink
        bot_token: your bot token
        chat_id: your chat id
    - discord_sink:
        name: discord_sink
        url: discord_webhook_url
    - jira_sink:
        name: personal_jira_sink
        url: https://workspace.atlassian.net
        username: username
        api_key: api_key
        dedups: (OPTIONAL)
            - fingerprint
        project_name: project_name
    - webhook_sink:
        name: webhook_sink
        url: "https://my-webhook-service.com/robusta-alerts"

More information about all that available Sinks can be found :ref:`here <Sinks>`

Sink matchers
---------------

Sinks can be configured to only report certain findings. If a finding matches more than one sink, it
will be sent to each one.

Each matcher can be a regular expression or a list of exact values.
If there is more than one rule, **all** the rules must match for a finding to be sent.

.. code-block:: yaml

    sinksConfig:
    - slack_sink:
        name: test_slack_sink
        slack_channel: test-notifications
        api_key: secret-key
        match:
          # match "dev" or "test" namespaces
          namespace:
          - dev
          - test
          # match any node containing the "test-node" substring
          node: test-node
    - slack_sink:
        name: prod_slack_sink
        slack_channel: prod-notifications
        api_key: secret-key
        match:
          # match the "prod" namespace exactly
          namespace: ^prod$
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

Supported attributes:
  - ``title``: e.g. ``Crashing pod crash-pod in namespace default``
  - ``identifier``: e.g. ``report_crash_loop`` [#f1]_
  - ``severity``: one of ``INFO``, ``LOW``, ``MEDIUM``, ``HIGH``
  - ``type``: one of ``ISSUE``, ``CONF_CHANGE``, ``HEALTH_CHECK``, ``REPORT``
  - ``kind``: one of ``deployment``, ``node``, ``pod``, ``job``, ``daemonset``
  - ``source``: one of ``NONE``, ``KUBERNETES_API_SERVER``, ``PROMETHEUS``, ``MANUAL``, ``CALLBACK``
  - ``namespace``: the Kubernetes object namespace
  - ``node`` : the Kubernetes node name
  - ``name`` : the Kubernetes object name

The regular expressions must be in the `Python re module format <https://docs.python.org/3/library/re.html#regular-expression-syntax>`_.

.. rubric:: Footnotes

.. [#f1] This is equivalent to ``Finding.aggregation_key`` which is set by each playbook that generates results. For now you'll have to check a playbook's source code to see what the value should be. For example, the `resource_babysitter playbook  <https://github.com/robusta-dev/robusta/blob/master/playbooks/robusta_playbooks/babysitter.py#L66>`_  sets a value of ``ConfigurationChange/KubernetesResource/Change``
