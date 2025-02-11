.. _sink-matchers:

.. _sink-scope-matching:

Routing Alerts To Specific Sinks
################################

This guide covers routing notifications to specific sinks by defining a ``scope``.

Sinks in Robusta determine where notifications are sent (e.g. Slack, email). 
By defining scopes, you can send notifications to different channels based on severity, namespace, and other conditions.

Inclusion Scopes
---------------------

If ``scope.include`` is defined, sinks will only receive matching notifications.

For example, to only send notifications with severity HIGH:

.. code-block:: yaml

    sinksConfig:
    - slack_sink:
        name: slack_urgent
        slack_channel: urgent
        api_key: secret-key
        scope:
          include:
            - severity: HIGH

For all attributes that can go inside ``include``, refer to :ref:`Scope Reference`.

An undefined include section will effectively include all alerts.

Exclusion Scopes
-------------------

If ``scope.exclude`` is defined, sinks will skip matching notifications.

This can be combined with ``scope.include``. For example, we can include notifications from namespace ``default`` but ignore specific notifications by name even in that namespace.

.. code-block:: yaml

    sinksConfig:
    - slack_sink:
        name: prod_sink
        slack_channel: prod-notifications
        api_key: secret-key
        scope:
          include:
            - namespace: default
          exclude:
            # regardless of the include sections, this will drop all alerts with name CrashLoopBackoff or ImagePullBackoff
            - identifier: [CrashLoopBackoff, ImagePullBackoff]

The general rule is that a notification must match **one of** the ``include`` sections, and **must not match all** the ``exclude`` sections.

You can use the same attributes in ``exclude`` as ``include`` - refer to :ref:`Scope Reference`.

An undefined ``exclude`` section will not exclude anything.

Stop Further Notifications
---------------------------

When using multiple sinks, **notifications are sent to all matching sinks by default**.

To stop sending notifications after a match, set ``stop: true``.

You can use ``stop`` to define a **fallback sink**:

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
        name: fallback_sink
        slack_channel: all-other-notifications
        api_key: secret-key

Note that the order of sinks matters! The first sink that matches a notification will receive it. That sink's ``stop`` value will determine if further sinks have a chance to receive the notification.

Advanced Scope Conditions
--------------------------

Mapping Prometheus Alerts to Kubernetes Resources
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
In Kubernetes environments, Robusta automatically maps Prometheus alerts to Kubernetes resources according to alert labels.
This lets you route alerts not only based on Prometheus metric labels, but also based on Kubernetes metadata.

For example, to route a Prometheus ``KubePodCrashLooping`` alert based on the related pod's ``app.kubernetes.io/name`` label:

.. code-block:: yaml

    sinksConfig:
    - slack_sink:
        name: test_sink
        slack_channel: test-notifications
        api_key: secret-key
        scope:
          include:
            - identifier: "KubePodCrashLooping"
              labels: "app.kubernetes.io/name=my-app"

Note that we routed based on Kubernetes metadata, not present in Prometheus itself!

.. details:: How does Robusta map Prometheus alerts to Kubernetes resources?

  Robusta uses alert labels to map Prometheus alerts to Kubernetes resources.

  For example, if a Prometheus alert has labels ``pod=my-pod`` and ``namespace=foo``, Robusta will fetch the relevant Kubernetes pod and associate it with the alert.
  
  If an alert has a label ``deployment=my-deployment``, Robusta will do something similar for Deployments. And so on.

  This mapping is done automatically, but can be customized if needed. For more details, refer to :ref:`Relabel Prometheus Alerts`.

AND Logic
^^^^^^^^^^^

In the following example, we define a sink that matches notifications which are both high-severity and in namespace ``prod``:

.. code-block:: yaml

    sinksConfig:
    - slack_sink:
        name: test_sink
        slack_channel: high-severity-and-prod
        api_key: secret-key
        scope:
          include:
            - namespace: prod
              severity: HIGH

Important: there is no dash character before ``severity``. As we'll see in the next section, this is the difference between AND/OR syntax.

OR Logic
^^^^^^^^^^^

To use OR logic, use multiple list elements inside the ``include`` block (each element starting with ``-``).

.. code-block:: yaml

    sinksConfig:
    - slack_sink:
        name: test_sink
        slack_channel: high-severity-or-prod
        api_key: secret-key
        scope:
          include:
            # OR between both conditions
            - namespace: prod
            - severity: HIGH

Important: note the dash character in``- severity``. This dash is critical as it separates the two conditions by OR.

.. details:: Understanding the Syntax for AND vs OR

  In the above examples, the difference between AND/OR is a single character - an extra dash (``-``).
  This is due to how YAML works.
  
  The above AND example is equivalent to the following JSON:

  .. code-block:: json

      "include": [
        {"namespace": "prod", "severity": "HIGH"}
      ]

  Whereas the OR example is equivalent to:

  .. code-block:: json

      "include": [
        {"namespace": "prod"},
        {"severity": "HIGH"}
      ]

  Each item in the ``include`` list is a set of AND conditions, whereas there is OR between each list element.

  In short, make sure you're careful with ``-`` characters when defining your rules!

Combining AND/OR Logic
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can define complex conditions, such as *HIGH severity notifications from staging + all alerts from prod*:

.. code-block:: yaml

    sinksConfig:
    - slack_sink:
        name: high-severity-staging-or-prod
        slack_channel: high-severity-staging-or-prod
        api_key: secret-key
        scope:
          # define 2 include elements, with an OR between them
          include:
            # this is the first include element - made up of two conditions with AND between them
            - namespace: staging
              severity: HIGH

            # this is the 2nd include element, with a single condition
            - namespace: prod

Matching Lists of Values
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The following will match any value in the list (either ``prod`` or ``default``):

.. code-block:: yaml

    sinksConfig:
    - slack_sink:
        name: test_sink
        slack_channel: test-notifications
        api_key: secret-key
        scope:
          include:
            - namespace: [prod, default]

This is equivalent to:

.. code-block:: yaml

    sinksConfig:
    - slack_sink:
        name: test_sink
        slack_channel: test-notifications
        api_key: secret-key
        scope:
          include:
            - namespace: prod
            - namespace: default

Using Regexes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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

Kubernetes Label Selectors
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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

Testing Alert Routing
----------------------

.. tip::
   Use the Robusta UI to test your alert routing rules by `simulating an alert <https://platform.robusta.dev/simulate-alert/>`_.

Scope Reference
-----------------

Here is the complete list of attributes that can be used in ``include`` / ``exclude`` sections:

+---------------------+-----------------------------------------------------------+------------------------------------------+
| **Attribute**       | **Value**                                                 | **Notes**                                |
+=====================+===========================================================+==========================================+
| ``identifier``      | For Prometheus alerts, the alert name - e.g.              |                                          |
|                     | ``KubePodCrashLooping``                                   |                                          |
+---------------------+-----------------------------------------------------------+------------------------------------------+
| ``title``           | Title of the notification. e.g.                           |                                          |
|                     | ``Crashing pod foo in namespace default``                 |                                          |
+---------------------+-----------------------------------------------------------+------------------------------------------+
| ``name``            | Kubernetes object name.                                   | For Prometheus alerts, automatically     |
|                     |                                                           | determined by alert labels like          |
|                     |                                                           | ``pod`` or ``deployment``                |
+---------------------+-----------------------------------------------------------+------------------------------------------+
| ``namespace``       | Kubernetes object namespace.                              | For Prometheus alerts, automatically     |
|                     |                                                           | determined by ``namespace`` label        |
+---------------------+-----------------------------------------------------------+------------------------------------------+
| ``node``            | Kubernetes node name.                                     | For Prometheus alerts,                   |
|                     |                                                           | determined by the alert labels ``node``  |
|                     |                                                           | or ``instance``, with automatic          | 
|                     |                                                           | normalization to node-name if the label  |
|                     |                                                           | had an IP:PORT value as if common in     |
+---------------------+-----------------------------------------------------------+------------------------------------------+
| ``severity``        | One of ``INFO``, ``LOW``, ``MEDIUM``, ``HIGH``.           |                                          |
+---------------------+-----------------------------------------------------------+------------------------------------------+
| ``type``            | One of ``ISSUE``, ``CONF_CHANGE``,                        |                                          |
|                     | ``HEALTH_CHECK``, ``REPORT``.                             |                                          |
+---------------------+-----------------------------------------------------------+------------------------------------------+
| ``kind``            | Kubernetes resource type. One of ``deployment``, ``node``,| For Prometheus alerts, automatically     |
|                     | ``pod``, ``job``, ``daemonset``.                          | determined by alert labels               |
+---------------------+-----------------------------------------------------------+------------------------------------------+
| ``source``          | One of ``NONE``, ``KUBERNETES_API_SERVER``,               |                                          |
|                     | ``PROMETHEUS``, ``MANUAL``, ``CALLBACK``.                 |                                          |
+---------------------+-----------------------------------------------------------+------------------------------------------+
| ``labels``          | Same as Kubernetes selectors: a comma-separated list of   | Can refer to both Kubernetes resource    |
|                     | ``key=val`` pairs with AND between them. e.g.,            | labels  and Prometheus alert             |
|                     | ``foo=bar,instance=123``. Supports regex in the value like| labels.             Prometheus values    |
|                     | ``foo=x.*``                                               | are prioritized when both exist.         |
+---------------------+-----------------------------------------------------------+------------------------------------------+
| ``annotations``     | Same as Kubernetes selectors: a comma-separated list of   | Can refer to both Kubernetes resource    |
|                     | ``key=val`` pairs with AND between them. e.g.             | annotations and Prometheus alert         |
|                     | ``app.kubernetes.io/name=prometheus``. Supports regex in  |        annotations. Prometheus values    |
|                     | the value.                                                | are prioritized when both exist.         |
+---------------------+-----------------------------------------------------------+------------------------------------------+
| ``namespace_labels``| Labels on the Kubernetes namespace containing this object.| Same matching syntax as ``labels``. For  |
|                     |                                                           | performance reasons, namespace label     |
|                     |                                                           | information is cached for 30 minutes by  |
|                     |                                                           | default. If you change namespace labels  |
|                     |                                                           | and want to reflect this change          |
|                     |                                                           | immediately in Robusta's scope mechanism,|
|                     |                                                           | you can restart the robusta-runner pod.  |
+---------------------+-----------------------------------------------------------+------------------------------------------+

.. .. details:: How do I find the ``identifier`` value to use in a match block? (deprecated)
..    For Prometheus alerts, it's always the alert name.
..    .. TODO: update after we finish our improvements here:
..    .. For builtin APIServer alerts, it can vary, but common values are ``CrashLoopBackoff``, ``ImagePullBackoff``, ``ConfigurationChange/KubernetesResource/Change``, and ``JobFailure``.
..    For custom playbooks, it's the value you set in :ref:`create_finding<create_finding>` under ``aggregation_key``.
..    Ask us in Slack if you need help.

When processing the ``scope`` block, the following rules apply:

#. If the notification is **excluded** by any of the sink ``scope`` excludes - drop it
#. If the notification is **included** by any of the sink ``scope`` includes - accept it
#. If the notification is **included** by any of the sink ``matchers`` (deprecated) - accept it

Alternative Routing Methods
-------------------------------

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