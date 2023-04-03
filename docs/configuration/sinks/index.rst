:hide-toc:

Sinks
======

.. toctree::
   :hidden:
   :maxdepth: 1

   slack
   telegram
   discord
   kafka
   DataDog
   ms-teams
   mattermost
   webhook
   webex
   Opsgenie
   VictorOps
   PagerDuty

Messages from Robusta can be sent to one or more destinations, which we call *sinks*.

Supported sinks
^^^^^^^^^^^^^^^^^^^^^
Click on a sink for setup instructions.

.. grid:: 1 1 2 3
    :gutter: 3

    .. grid-item-card:: :octicon:`cpu;1em;` Slack
        :class-card: sd-bg-light sd-bg-text-light
        :link: slack
        :link-type: doc


    .. grid-item-card:: :octicon:`cpu;1em;` Telegram
        :class-card: sd-bg-light sd-bg-text-light
        :link: telegram
        :link-type: doc


    .. grid-item-card:: :octicon:`cpu;1em;` Discord
        :class-card: sd-bg-light sd-bg-text-light
        :link: discord
        :link-type: doc


    .. grid-item-card:: :octicon:`cpu;1em;` Kafka
        :class-card: sd-bg-light sd-bg-text-light
        :link: kafka
        :link-type: doc


    .. grid-item-card:: :octicon:`cpu;1em;` DataDog
        :class-card: sd-bg-light sd-bg-text-light
        :link: DataDog
        :link-type: doc

    .. grid-item-card:: :octicon:`cpu;1em;` MS-teams
        :class-card: sd-bg-light sd-bg-text-light
        :link: ms-teams
        :link-type: doc

    .. grid-item-card:: :octicon:`cpu;1em;` Mattermost
        :class-card: sd-bg-light sd-bg-text-light
        :link: mattermost
        :link-type: doc

    .. grid-item-card:: :octicon:`cpu;1em;` Webhook
        :class-card: sd-bg-light sd-bg-text-light
        :link: webhook
        :link-type: doc

    .. grid-item-card:: :octicon:`cpu;1em;` OpsGenie
        :class-card: sd-bg-light sd-bg-text-light
        :link: Opsgenie
        :link-type: doc

    .. grid-item-card:: :octicon:`cpu;1em;` VictorOps
        :class-card: sd-bg-light sd-bg-text-light
        :link: VictorOps
        :link-type: doc

    .. grid-item-card:: :octicon:`cpu;1em;` PagerDuty
        :class-card: sd-bg-light sd-bg-text-light
        :link: PagerDuty
        :link-type: doc
    .. grid-item-card:: :octicon:`cpu;1em;` Webex
        :class-card: sd-bg-light sd-bg-text-light
        :link: webex
        :link-type: doc


**Need support for something not listed here?** `Tell us and we'll add it. <https://github.com/robusta-dev/robusta/issues/new?assignees=&labels=&template=feature_request.md&title=New%20Sink:>`_

Defining Sinks
^^^^^^^^^^^^^^^^^^
Sinks are defined in Robusta's Helm chart, using the ``sinksConfig`` value. For example:

.. code-block:: yaml

    sinksConfig:
    - ms_teams_sink:                  # sink type
        name: my_teams_sink           # arbitrary name
        webhook_url: <placeholder>    # a sink-specific parameter
        match: {}                     # optional routing rules (see below)

Routing alerts to specific sinks
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Sinks can be configured to only send certain notifications.

For example, let's send messages to Slack only for HIGH severity notifications in the ``dev`` or ``test`` namespace.

.. code-block:: yaml

    sinksConfig:
    - slack_sink:
        name: test_sink
        slack_channel: test-notifications
        api_key: secret-key
        match:
          namespace: [dev, test]
          severity: [HIGH]

A few guidelines:

* If notifications match more than one sink, they are sent to each one
* If a sink has more than one rule, all rules must match for notifications to be sent

Every rule supports both regular expressions and a list of exact values. For example:

.. code-block:: yaml

    sinksConfig:
    - slack_sink:
        name: prod_slack_sink
        slack_channel: prod-notifications
        api_key: secret-key
        match:
          namespace: ^prod$ # match the "prod" namespace exactly


For practical examples, see the Notification Routing tutorial.

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

Per-playbook routing
^^^^^^^^^^^^^^^^^^^^^^^^
The first method defines a routing rule when notifications are generated. This method is most when you define customPlaybooks:

If a playbook doesn't specify a sink then output will be sent to the default sinks. A sink is considered default
if it has the field `default: true` in the YAML.

Sink-specific behaviour
^^^^^^^^^^^^^^^^^^^^^^^^^
At the moment, there are two sinks in Robusta that support special behaviour:

* Slack - supports action-buttons for responding to alerts
* Robusta UI - when enabled, this adds "Investigate" and "Silence" buttons to alerts
