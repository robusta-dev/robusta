.. _sink-matchers:

.. _sink-scope-matching:

Routing Alerts To Specific Sinks
####################################

You can define routing-rules using a :ref:`scope block <All Scope Options>`.

A Basic Example
^^^^^^^^^^^^^^^^^^

To send high-severity alerts to Slack (and not other alerts), add a ``scope`` to your slack sink:

.. code-block:: yaml

    sinksConfig:
    - slack_sink:
        name: test_sink
        slack_channel: test-notifications
        api_key: secret-key
        scope:
          include:
            - severity: HIGH

See below for :ref:`All Scope Options`.

AND Between Two Conditions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

More complex logic is possible. For example, we can match high-severity alerts from the ``prod`` namespace:

.. code-block:: yaml

    sinksConfig:
    - slack_sink:
        name: test_sink
        slack_channel: test-notifications
        api_key: secret-key
        scope:
          include:
            # AND between both conditions
            - namespace: prod
              severity: HIGH

Note that namespace and severity appear within a single YAML list element that starts with a dash (``-``). 
There is no dash (``-``) character prior to ``severity``. (If this was written as ``- severity`` then it would be treated as 2 separate conditions with an OR between them. See below.)

OR Between Two Conditions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If there are multiple list elements (each starting with ``-``) inside the ``include`` block, they are combined with OR logic:

.. code-block:: yaml

    sinksConfig:
    - slack_sink:
        name: prod_slack_sink
        slack_channel: prod-notifications
        api_key: secret-key
        scope:
          # define 2 include elements, with an OR between them
          include:
            - namespace: default
            - namespace: bla

You can combine AND syntax with OR syntax:

.. code-block:: yaml

    sinksConfig:
    - slack_sink:
        name: prod_slack_sink
        slack_channel: prod-notifications
        api_key: secret-key
        scope:
          # define 2 include elements, with an OR between them
          include:
            # this is a single include section. to match it, the alert's subject must be in namespace 'default' and have name 'foo'
            - namespace: default
              name: "foo"

            # this is another include section. to match it, the alert's subject must be in namespace 'bla'
            - namespace: bla

Exclusion Rules
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In addition to inclusion rules, you can add exclusion rules:

.. code-block:: yaml

    sinksConfig:
    - slack_sink:
        name: prod_slack_sink
        slack_channel: prod-notifications
        api_key: secret-key
        scope:
          # only include alerts from namespace default
          include:
            - namespace: default
 
          exclude:
            # regardless of the include sections, this will drop all alerts with name CrashLoopBackoff or ImagePullBackoff
            - identifier: [CrashLoopBackoff, ImagePullBackoff]

The general rule is that an alert must match **one of** the ``include`` sections, and **must not match all** the ``exclude`` sections.

Special Syntax for Matching One of Many Values
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Each attribute can be a single value or a list of values:

.. code-block:: yaml

    sinksConfig:
    - slack_sink:
        name: test_sink
        slack_channel: test-notifications
        api_key: secret-key
        scope:
          include:
            # here we use a list with a single value
            - namespace: [prod]
            # this is equivalent to the above
            - namespace: prod
            # this would match EITHER the namespace 'prod' OR the namespace 'default'
            - namespace: [prod, default]

Using Regexes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can also use `regexes <https://docs.python.org/3/library/re.html#re.match>`_:

.. code-block:: yaml

    sinksConfig:
    - slack_sink:
        name: test_sink
        slack_channel: test-notifications
        api_key: secret-key
        scope:
          include:
            # this will match kube-system
            - namespace: kube-.*

Using Kubernetes Label Selectors
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can match on Kubernetes label selectors with special syntax:

.. code-block:: yaml

    sinksConfig:
    - slack_sink:
        name: prod_slack_sink
        slack_channel: prod-notifications
        api_key: secret-key
        scope:
          include:
            # label selectors are interpreted like Kubernetes - selectors separated by comma are ANDED together
            - labels: "instance=1,foo!=x.*"

.. tip::

    Using the Robusta UI, you can test alert routing by `Simulating an alert <https://platform.robusta.dev/simulate-alert/>`_.

All Scope Options
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
