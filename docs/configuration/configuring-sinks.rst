.. _sinks-overview:

Integrating Sinks
==========================

Robusta can send notifications to various destinations, called sinks. These are general settings for all sinks, please take a look at the specific sink guide for detailed instructions.

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
        scope: {}                     # optional routing rules
        match: {}                     # optional routing rules (deprecated; see below)
        default: true                 # optional (see below)

To add a sink, update ``sinksConfig`` according to the instructions in :ref:`Sinks Reference`. Then do a :ref:`Helm Upgrade <Simple Upgrade>`.

Integrate as many sinks as you like.

.. _sink-matchers:


Routing Alerts to Only One Sink
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
        scope:
          include:
            - namespace: production
        stop: true


Routing Alerts To Specific Sinks
***************************************

Define which messages a sink accepts using ``scope``.

For example, **Slack**  can be integrated to receive high-severity messages in a specific namespace. Other messages will not be sent to this **Slack** sink.

.. code-block:: yaml

    sinksConfig:
    - slack_sink:
        name: test_sink
        slack_channel: test-notifications
        api_key: secret-key
        scope:
          include: # more options available - see below
            - namespace: [prod]
              severity: HIGH

Each attribute expression used in the ``scope`` specification can be 1 item, or a list, where each is either a regex or an exact match

``Scope`` allows specifying a set of ``include`` and ``exclude`` sections:

.. code-block:: yaml

    sinksConfig:
    - slack_sink:
        name: prod_slack_sink
        slack_channel: prod-notifications
        api_key: secret-key
        scope:
        # AND between namespace and labels, but OR within each selector
          include:
            - namespace: default
              labels: "instance=1,foo!=x.*"
            - namespace: bla
              name:
              - foo
              - qux
          exclude:
            - type: ISSUE
              title: .*crash.*
            - name: bar[a-z]*


In order for a message to be sent to a ``Sink``, it must match **one of** the ``include`` sections, and **must not** match **all** the ``exclude`` sections.

When multiple attributes conditions are present, all must be satisfied.

The following attributes can be included in an ``include``/``excluded`` block:

- ``title``: e.g. ``Crashing pod foo in namespace default``
- ``name`` : the Kubernetes object name
- ``namespace``: the Kubernetes object namespace
- ``node`` : the Kubernetes node name
- ``severity``: one of ``INFO``, ``LOW``, ``MEDIUM``, ``HIGH``
- ``type``: one of ``ISSUE``, ``CONF_CHANGE``, ``HEALTH_CHECK``, ``REPORT``
- ``kind``: one of ``deployment``, ``node``, ``pod``, ``job``, ``daemonset``
- ``source``: one of ``NONE``, ``KUBERNETES_API_SERVER``, ``PROMETHEUS``, ``MANUAL``, ``CALLBACK``
- ``identifier``: e.g. ``CrashLoopBackoff``
- ``labels``: A comma separated list of ``key=val`` e.g. ``foo=bar,instance=123``
- ``annotations``: A comma separated list of ``key=val`` e.g. ``app.kubernetes.io/name=prometheus``

.. note::

    ``labels`` and ``annotations`` are both the Kubernetes resource labels and annotations
    (e.g. pod labels) and the Prometheus alert labels and annotations. If both contains the
    same label/annotation, the value from the Prometheus alert is preferred.


.. details:: How do I find the ``identifier`` value to use in a match block? (deprecated)

    For Prometheus alerts, it's always the alert name.

    .. TODO: update after we finish our improvements here:
    .. For builtin APIServer alerts, it can vary, but common values are ``CrashLoopBackoff``, ``ImagePullBackoff``, ``ConfigurationChange/KubernetesResource/Change``, and ``JobFailure``.

    For custom playbooks, it's the value you set in :ref:`create_finding<create_finding>` under ``aggregation_key``.

    Ask us in Slack if you need help.

By default, every message is sent to every matching sink. To change this behaviour, you can mark a sink as :ref:`non-default <Non-default sinks>`.

The top-level mechanism works as follows:

#. If the notification is **excluded** by any of the sink ``scope`` excludes - drop it
#. If the notification is **included** by any of the sink ``scope`` includes - accept it
#. If the notification is **included** by any of the sink ``matchers`` - accept it (Deprecated)

Any of (but not both) of the ``include`` and ``exclude`` may be left undefined or empty.
An undefined/empty ``include`` section will effectively allow all alerts, and an
undefined/empty ``exclude`` section will not exclude anything.

Inside the ``include`` and ``exclude`` section, at the topmost level, the consecutive
items act with the OR logic, meaning that it's enough to match a single item in the
list in order to allow/reject a message. The same applies to the items listed under
each attribute name.

Within a specific ``labels`` or ``annotations`` expression, the logic is ``AND``

.. code-block:: yaml

    ....
        scope:
          include:
            - labels: "instance=1,foo=x.*"
    .....

The above requires that the ``instance`` will have a value of ``1`` **AND** the ``foo`` label values starts with ``x``

Match Section (Deprecated)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Define which messages a sink accepts using *matchers*.

For example, Slack can be integrated to receive high-severity messages in a specific
namespace. Other messages will not be sent to Slack.

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
- ``identifier``: e.g. ``CrashLoopBackoff``
- ``labels``: A comma separated list of ``key=val`` e.g. ``foo=bar,instance=123``
- ``annotations``: A comma separated list of ``key=val`` e.g. ``app.kubernetes.io/name=prometheus``

.. note::

    ``labels`` and ``annotations`` are both the Kubernetes resource labels and annotations
    (e.g. pod labels) and the Prometheus alert labels and annotations. If both contains the
    same label/annotation, the value from the Prometheus alert is preferred.


.. details:: How do I find the ``identifier`` value to use in a match block? (deprecated)

    For Prometheus alerts, it's always the alert name.

    .. TODO: update after we finish our improvements here:
    .. For builtin APIServer alerts, it can vary, but common values are ``CrashLoopBackoff``, ``ImagePullBackoff``, ``ConfigurationChange/KubernetesResource/Change``, and ``JobFailure``.

    For custom playbooks, it's the value you set in :ref:`create_finding<create_finding>` under ``aggregation_key``.

    Ask us in Slack if you need help.

By default, every message is sent to every matching sink. To change this behaviour, you can mark a sink as :ref:`non-default <Non-default sinks>`.

Match Section (Deprecated): Matches Can Be Lists or Regexes
***********************************************************

*match* rules support both regular expressions and lists of exact values:

.. code-block:: yaml

    sinksConfig:
    - slack_sink:
        name: prod_slack_sink
        slack_channel: prod-notifications
        api_key: secret-key
        # AND between namespace and severity
        match:
          namespace: ^prod$                # match the "prod" namespace exactly
          severity: [HIGH, LOW]            # either HIGH or LOW (OR logic)

Regular expressions must be in `Python re module format <https://docs.python.org/3/library/re.html#regular-expression-syntax>`_, as passed to `re.match <https://docs.python.org/3/library/re.html#re.match>`_.

Match Section (Deprecated): Matching Labels and Annotations
***********************************************************

Special syntax is used for matching labels and annotations:

.. code-block:: yaml

    sinksConfig:
    - slack_sink:
        name: prod_slack_sink
        slack_channel: prod-notifications
        api_key: secret-key
        match:
          labels: "foo=bar,instance=123"   # both labels must match

The syntax is similar to Kubernetes selectors, but only `=` conditions are allowed, not `!=`

Match Section (Deprecated): Or Between Matches
**********************************************

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
          aggregation_key: "JobFailure"
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

Time-limiting sink activity
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

It is possible, for any sink, to set the schedule of its activation by specifying the ``activity`` field in its
configuration. You can specify multiple time spans, with specific days of the week and hours in these days that
the sink will be active. Outside of these specified time spans, the sink will not run - so for example Slack
messages will not be delivered.

An example of such a configuration is presented below:

.. code-block:: yml

    sinksConfig:
    - slack_sink:
        name: main_slack_sink
        slack_channel: robusta-notifications
        api_key: xoxb-your-slack-key
        activity:
          timezone: CET
          intervals:
          - days: ['mon', 'tue', 'sun']
            hours:
            - start: 10:00
              end: 11:00
            - start: 16:00
              end: 17:00
          - days: ['thr']
            hours:
            - start: 10:00
              end: 16:00
            - start: 16:05
              end: 23:00

Note that if the ``activity`` field is omitted, it is assumed that the sink will always be activated.
As seen above, each section under ``intervals`` may have multiple spans of time under the ``hours``
key. If the ``hours`` section is omitted for a given interval, it's assumed that the sink will be
active for all the specified days, irrespective of time.

Examples
^^^^^^^^^^^

🎓 :ref:`Route Alerts By Namespace`

🎓 :ref:`Route Alerts By Type`

🎓 :ref:`Routing with Exclusion Rules`

See Also
^^^^^^^^^^^^

🔔 :ref:`All Sinks <Sinks Reference>`

🎓 :ref:`Silencing Alerts`
