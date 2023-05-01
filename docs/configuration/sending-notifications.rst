.. _sinks-overview:

Configuring Notifications
==========================

Robusta can send notifications to various destinations, called sinks.

For a list of all sinks, refer to :ref:`Sinks Reference`.

To define rules that generate custom notifications, refer to :ref:`Defining Playbooks`.

Defining Sinks
^^^^^^^^^^^^^^^^^^
Sinks are defined in Robusta's Helm chart, using the ``sinksConfig`` value:

.. code-block:: yaml

    sinksConfig:
    - ms_teams_sink:                  # sink type
        name: my_teams_sink           # arbitrary name
        webhook_url: <placeholder>    # a sink-specific parameter
        match: {}                     # optional routing rules (see below)
        default: true                 # optional (see below)

To add a sink, update ``sinksConfig`` according to the instructions in :ref:`Sinks Reference`. Then do a :ref:`Helm Upgrade <Simple Upgrade>`.

Configure as many sinks as you like.

.. _sink-matchers:

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

The above example defines match conditions by both ``namespace`` and ``severity``. When multiple conditions are present, all must be satisfied.

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
        # AND between namespace and severity
        match:
          namespace: ^prod$ # match the "prod" namespace exactly
          severity: [HIGH, LOW] # either HIGH or LOW (or logic)

The following attributes can be included in a *match* block:

- ``title``: e.g. ``Crashing pod foo in namespace default``
- ``name`` : the Kubernetes object name
- ``namespace``: the Kubernetes object namespace
- ``node`` : the Kubernetes node name
- ``severity``: one of ``INFO``, ``LOW``, ``MEDIUM``, ``HIGH``
- ``type``: one of ``ISSUE``, ``CONF_CHANGE``, ``HEALTH_CHECK``, ``REPORT``
- ``kind``: one of ``deployment``, ``node``, ``pod``, ``job``, ``daemonset``
- ``source``: one of ``NONE``, ``KUBERNETES_API_SERVER``, ``PROMETHEUS``, ``MANUAL``, ``CALLBACK``
- ``identifier``: e.g. ``report_crash_loop`` [#f1]_

The regular expressions must be in the `Python re module format <https://docs.python.org/3/library/re.html#regular-expression-syntax>`_, as passed to `re.match <https://docs.python.org/3/library/re.html#re.match>`_.

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

Next Steps
^^^^^^^^^^^^

* :ref:`View a list of built-in sinks <Sinks Reference>`
* :ref:`See examples of routing rules in the tutorials<sink-matchers>`

.. rubric:: Footnotes

.. [#f1] This is equivalent to ``Finding.aggregation_key`` which is set by each playbook that generates results. For now, you must check a playbook's source code to see the value. For example, the `resource_babysitter playbook  <https://github.com/robusta-dev/robusta/blob/master/playbooks/robusta_playbooks/babysitter.py#L66>`_  sets a value of ``ConfigurationChange/KubernetesResource/Change``
