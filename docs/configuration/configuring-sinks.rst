.. _sinks-overview:

Configuring Sinks
==========================

Robusta can send notifications to various destinations, called sinks.

For a list of all sinks, refer to :ref:`Sinks Reference`.

Defining Sinks
^^^^^^^^^^^^^^^^^^
Sinks are defined in Robusta's Helm chart, using the ``sinksConfig`` value:

.. code-block:: yaml

    sinksConfig:
    - ms_teams_sink:                  # sink type
        name: my_teams_sink           # arbitrary name
        webhook_url: <placeholder>    # a sink-specific parameter
        stop: false                   # optional (see `Routing Alerts to only one Sink`)
        match: {}                     # optional routing rules (see below)
        default: true                 # optional (see below)

To add a sink, update ``sinksConfig`` according to the instructions in :ref:`Sinks Reference`. Then do a :ref:`Helm Upgrade <Simple Upgrade>`.

Configure as many sinks as you like.

.. _sink-matchers:


Routing Alerts to only one Sink
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

By default, alerts are sent to all sinks that matches the alerts.

To prevent sending alerts to more sinks after the current one, you can specify ``stop: true``

The sinks evaluation order, is the order defined in ``generated_values.yaml``.

.. code-block:: yaml

    sinksConfig:
    - slack_sink:
        name: production_sink
        slack_channel: production-notifications
        api_key: secret-key
        match:
          namespace: production
        stop: true


Routing Alerts to Specific Sinks
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Define which messages a sink accepts using *matchers*.

For example, Slack can be configured to receive high-severity messages in a specific namespace. Other messages will not be sent to Slack.

.. code-block:: yaml

    sinksConfig:
    - slack_sink:
        name: test_sink
        slack_channel: test-notifications
        api_key: secret-key
        match:
          namespace: [prod]
          severity: [HIGH]
          # more options available - see below

When multiple match conditions are present, all must be satisfied.

The following attributes can be included in a *match* block:

- ``title``: e.g. ``Crashing pod foo in namespace default``
- ``name`` : the Kubernetes object name
- ``namespace``: the Kubernetes object namespace
- ``node`` : the Kubernetes node name
- ``severity``: one of ``INFO``, ``LOW``, ``MEDIUM``, ``HIGH``
- ``type``: one of ``ISSUE``, ``CONF_CHANGE``, ``HEALTH_CHECK``, ``REPORT``
- ``kind``: one of ``deployment``, ``node``, ``pod``, ``job``, ``daemonset``
- ``source``: one of ``NONE``, ``KUBERNETES_API_SERVER``, ``PROMETHEUS``, ``MANUAL``, ``CALLBACK``
- ``identifier``: e.g. ``report_crash_loop``
- ``labels``: A comma separated list of ``key=val`` e.g. ``foo=bar,instance=123``
- ``annotations``: A comma separated list of ``key=val`` e.g. ``app.kubernetes.io/name=prometheus``

.. note::

    ``labels`` and ``annotations`` are both the Kubernetes resource labels and annotations (e.g. pod labels) and the Prometheus alert labels and annotations.
    If both contains the same label/annotation, the value from the Prometheus alert is preferred.


.. details:: How do I find the ``identifier`` value to use in a match block?

    For Prometheus alerts, it's always the alert name.

    .. TODO: update after we finish our improvements here:
    .. For builtin APIServer alerts, it can vary, but common values are ``report_crash_loop``, ``image_pull_backoff_reporter``, ``ConfigurationChange/KubernetesResource/Change``, and ``job_failure``.

    For custom playbooks, it's the value you set in :ref:`create_finding<create_finding>` under ``aggregation_key``.

    Ask us in Slack if you need help.

By default, every message is sent to every matching sink. To change this behaviour, you can mark a sink as :ref:`non-default <Non-default sinks>`.

Matches Can Be Lists Or Regexes
********************************************

Every *match* rule supports both regular expressions and a list of exact values:

.. code-block:: yaml

    sinksConfig:
    - slack_sink:
        name: prod_slack_sink
        slack_channel: prod-notifications
        api_key: secret-key
        # AND between namespace and severity and labels
        match:
          namespace: ^prod$ # match the "prod" namespace exactly
          severity: [HIGH, LOW] # either HIGH or LOW (or logic)
          labels: "foo=bar,instance=123"

Regular expressions must be in `Python re module format <https://docs.python.org/3/library/re.html#regular-expression-syntax>`_, as passed to `re.match <https://docs.python.org/3/library/re.html#re.match>`_.


Or Between Matches
********************************************

You can use `Or` between *match* rules:

.. code-block:: yaml

    sinksConfig:
    - slack_sink:
        name: prod_slack_sink
        slack_channel: prod-notifications
        api_key: secret-key
        # AND between namespace and labels, but or within each selector
        match:
          namespace:
          - default
          - robusta
          labels:
          - "instance=123"
          - "instance=456"

The above will match a resource from namespace (default *or* robusta) *and* label (instance=123 *or* instance=456)

Alternative Routing Methods
************************************************

For :ref:`customPlaybooks <defining-playbooks>`, there is another option for routing notifications.

Instead of using sink matchers, you can set the *sinks* attribute per playbook:

.. code-block:: yaml

    customPlaybooks:
    - triggers:
      - on_job_failure: {}
      actions:
      - create_finding:
          aggregation_key: "job_failure"
          title: "Job Failed"
      - job_info_enricher: {}
      - job_events_enricher: {}
      - job_pod_enricher: {}
      sinks:
        - "some_sink"
        - "some_other_sink"

Notifications generated this way are sent exclusively to the specified sinks. They will still be filtered by matchers.

Non-Default Sinks
*********************************

To prevent a sink from receiving most notifications, you can set ``default: false``. In this case, notifications will be
routed to the sink only from :ref:`customPlaybooks that explicitly name this sink <Alternative Routing Methods>`.

Here too, matchers apply as usual and perform further filtering.

Examples
^^^^^^^^^^^

🎓 :ref:`Route Alerts By Namespace`

🎓 :ref:`Route Alerts By Type`

🎓 :ref:`Routing with Exclusion Rules`

See Also
^^^^^^^^^^^^

🔔 :ref:`All Sinks <Sinks Reference>`

🎓 :ref:`Silencing Alerts`
