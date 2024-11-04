.. _sinks-overview:

Notification 101
==========================

Robusta can send notifications to various destinations, called sinks. For a list of all sinks, refer to :ref:`Sinks Reference`.

Defining Sinks
^^^^^^^^^^^^^^^^^^
Sinks are defined in Robusta's Helm chart, using the ``sinksConfig`` value.

For example, lets add a :ref:`Microsoft Teams <MS Teams sink>`:

.. code-block:: yaml

    sinksConfig:
    - ms_teams_sink:                  # sink type
        name: my_teams_sink           # arbitrary name
        webhook_url: <placeholder>    # a sink-specific parameter
        stop: false                   # optional (see `Routing Alerts to only one Sink`)
        scope: {}                     # optional routing rules
        default: true                 # optional (see below)

Many sinks have unique parameters which can be found under :ref:`Sinks Reference`.

Defining Multiple Sinks
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
You can define multiple sinks and by default, notifications will be sent to all of them.

If you'd like to selectively send notifications to different sinks, you can define :ref:`routing rules <sink-scope-matching>`.

In the following example, we define a :ref:`Slack sink <Slack>` and a :ref:`MS Teams sink <MS Teams>` without any routing rules, so both sinks receive all notifications:

.. code-block:: yaml

    sinksConfig:
    - slack_sink:
        name: my_slack_sink
        slack_channel: my-channel
        api_key: secret-key
    - ms_teams_sink:
        name: my_teams_sink
        webhook_url: <placeholder>

.. _sink-matchers:

.. _sink-scope-matching:

Routing Alerts To Specific Sinks
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can define routing-rules using a ``scope`` block.

For example, to send only high-severity alerts to Slack:

.. code-block:: yaml

    sinksConfig:
    - slack_sink:
        name: test_sink
        slack_channel: test-notifications
        api_key: secret-key
        scope:
          include:
            - severity: HIGH

More complex routing rules are possible. For example, we match only high-severity alert from the ``prod`` namespace:

.. code-block:: yaml

    sinksConfig:
    - slack_sink:
        name: test_sink
        slack_channel: test-notifications
        api_key: secret-key
        scope:
          include:
            # AND between both conditions
            - namespace: [prod]
              severity: HIGH

Each attribute used in ``scope.include`` can be a single item, or a list. Both exact matches and `regexes <https://docs.python.org/3/library/re.html#re.match>`_ are supported.

Here is a more complex example showing multiple ``include`` and ``exclude`` sections:

.. code-block:: yaml

    sinksConfig:
    - slack_sink:
        name: prod_slack_sink
        slack_channel: prod-notifications
        api_key: secret-key
        scope:
          # define 3 include sections, with an OR between them
          include:
            # this is a single include section. for an include section to match, the alert must match EVERYTHING in it (both namespace and name)
            - namespace: default
              name: ["foo"]

            # this is another include section - the alert will match if it matches this include section or the one above (but within each section, all conditions must be satisfied)
            - namespace: bla
              # when multiple values are provided for a given attribute, they are ORed together
              name: ["bar", "baz"]

            # this is yet a third include section (ORed with the previous two)
            # label selectors are interpreted as in Kubernetes - meaning selectors separated by comma are ANDED together
            - labels: "instance=1,foo!=x.*"

          # define 2 exclude sections, with an AND between them - all exclude sections must not match
          exclude:
            # again, within a single include/exclude section, all conditions must be satisfied for the section to match
            - type: ISSUE
              title: .*crash.*
            - name: bar[a-z]*


In the above example, an alert must match **one of** the ``include`` sections, and **must not match all** the ``exclude`` sections.

.. tip::

    Using the Robusta UI, you can test alert routing by `Simulating an alert <https://platform.robusta.dev/simulate-alert/>`_.

Reference for all Scope Options
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Here is the complete list of attributes that can be used in ``include`` / ``exclude`` sections:

- ``title``: e.g. ``Crashing pod foo in namespace default``
- ``name`` : the Kubernetes object name
- ``namespace``: the Kubernetes object namespace
- ``namespace_labels``: labels assigned to the namespace; matching these is done in the same way as matching ``labels`` (see below)
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

.. note::

    For performance reasons, the namespace information used for matching ``namespace_labels``
    is cached (with a default cache timeout of 30 minutes). If you change namespace labels
    and want these changes to be immediately reflected in the sink ``scope`` matching
    mechanism, you will need to manually restart the Robusta runner.

.. details:: How do I find the ``identifier`` value to use in a match block? (deprecated)

    For Prometheus alerts, it's always the alert name.

    .. TODO: update after we finish our improvements here:
    .. For builtin APIServer alerts, it can vary, but common values are ``CrashLoopBackoff``, ``ImagePullBackoff``, ``ConfigurationChange/KubernetesResource/Change``, and ``JobFailure``.

    For custom playbooks, it's the value you set in :ref:`create_finding<create_finding>` under ``aggregation_key``.

    Ask us in Slack if you need help.

When processing the ``scope`` block, the following rules apply:

#. If the notification is **excluded** by any of the sink ``scope`` excludes - drop it
#. If the notification is **included** by any of the sink ``scope`` includes - accept it
#. If the notification is **included** by any of the sink ``matchers`` (deprecated) - accept it

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

Fall-through routing
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Sinks are matched in the order they are defined in ``generated_values.yaml``.

To prevent sending alerts to more sinks after the current one matches, you can specify ``stop: true`` in the sink.

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

    # because the previous sink sets stop: true, this sink will only receive alerts not matched by the previous sink
    - slack_sink:
        name: non_production_sink
        slack_channel: non-production-notifications
        api_key: secret-key

Alternative Routing Methods
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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

If you use this method, you can set ``default: false`` in the sink definition and it will be ignored for all notifications except those from custom playbooks that explicitly name this sink.

More Examples
^^^^^^^^^^^

🎓 :ref:`Route Alerts By Namespace`

🎓 :ref:`Route Alerts By Type`

🎓 :ref:`Routing with Exclusion Rules`

See Also
^^^^^^^^^^^^

🔔 :ref:`All Sinks <Sinks Reference>`

🎓 :ref:`Silencing Alerts`
