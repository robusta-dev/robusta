Helm Releases Monitoring
#############################

Robusta can monitor your Helm releases, notify you about updates, and take actions in response. For example, you can:

* Get notified in Slack when a Helm release fails
* Get notified in MSTeams if a Helm release is pending for more than X seconds
* Send details on your Helm history to external tools

…and more

Prerequisites
---------------
To use Helm Triggers, the :ref:`Robusta UI` sink must be enabled..

Triggers
-----------

The following triggers are available:

.. _on_helm_release_unhealthy:

.. details:: on_helm_release_unhealthy


    ``on_helm_release_unhealthy`` triggers when a Helm release remains unhealthy for over ``duration`` seconds.  Unhealthy states are: ``uninstalling``, ``pending-install``, ``pending-upgrade``, and ``pending-rollback``.


    **Available options**:

    * ``rate_limit``: Limit firing to once every `rate_limit` seconds.
    * ``names``: List of Helm release names for this trigger to monitor. Leaving this field empty monitors all release names in the namespace. Optional.
    * ``namespace``: The Helm release namespace for this trigger to monitor. Leaving this field empty monitors all release namespace in the cluster. Optional.
    * ``duration``: Minimum time, in seconds, that a release must remain unhealthy before the trigger fires. If the unhealthy state lasts less than this duration, the trigger won't fire. Default value is 900 seconds (15 minutes). Optional.

    .. admonition:: Example

        Monitor the ``demo-app`` Helm release in the ``default`` namespace. Send notifications when it is unhealthy for more than 15 minutes (900 seconds). Do not send further notifications for at least 4 hours (14400 seconds).

        .. code-block:: yaml

            customPlaybooks:
              - triggers:
                - on_helm_release_unhealthy:
                    names: ["demo-app"] # optional
                    namespace: "default" # optional
                    duration: 900 # optional
                    rate_limit: 14400
                actions:
                  - helm_status_enricher: {}


    .. image:: /images/helm-release-unhealthy.png
      :width: 1000
      :align: center


.. _on_helm_release_fail:

.. details:: on_helm_release_fail

    ``on_helm_release_fail` is triggered when a Helm release enters a ``failed`` state. This is a one-time trigger, meaning that it only fires once when the release fails.

    **Available options**:

    * ``names``: List of Helm release names for this trigger to monitor. Leaving this field empty monitors all release names in the namespace. Optional.
    * ``namespace``: The Helm release namespace for this trigger to monitor. Leaving this field empty monitors all release namespace in the cluster. Optional.

    .. admonition:: Example

        Monitor the ``demo-app`` Helm release in the ``default`` namespace and send notifications when it is failing.

        .. code-block:: yaml

            customPlaybooks:
              - triggers:
                - on_helm_release_fail:
                    names: ["demo-app"] # optional
                    namespace: "default" # optional
                actions:
                  - helm_status_enricher: {}

    .. image:: /images/helm-release-failed.png
      :width: 1000
      :align: center

.. _on_helm_release_deploy:

.. details:: on_helm_release_deploy

    The ``on_helm_release_deploy`` event is triggered when a Helm release enters a ``deployed`` state. This is a one-time trigger, meaning that it only fires once when the release is deployed.

    **Available options**:

    * ``names``: List of Helm release names for this trigger to monitor. Leaving this field empty monitors all release names in the namespace. Optional.
    * ``namespace``: The Helm release namespace for this trigger to monitor. Leaving this field empty monitors all release namespace in the cluster. Optional.

    .. admonition:: Example

        Monitor the ``demo-app`` Helm release in the ``default`` namespace and send notifications when it is deployed.

        .. code-block:: yaml

            customPlaybooks:
              - triggers:
                - on_helm_release_deploy:
                    names: ["demo-app"] # optional
                    namespace: "default" # optional
                actions:
                  - helm_status_enricher: {}

    .. image:: /images/helm-release-deployed.png
      :width: 1000
      :align: center


.. _on_helm_release_uninstall:

.. details:: on_helm_release_uninstall

    The ``on_helm_release_uninstall`` event is triggered when a Helm release enters a ``uninstalled`` state. This is a one-time trigger, meaning that it only fires once when the release is uninstalled.

    **Available options**:

    * ``names``: List of Helm release names for this trigger to monitor. Leaving this field empty monitors all release names in the namespace. Optional.
    * ``namespace``: The Helm release namespace for this trigger to monitor. Leaving this field empty monitors all release namespace in the cluster. Optional.

    .. admonition:: Example

        Monitor the ``demo-app`` Helm release in the ``default`` namespace and send notifications when it is uninstalled.

        .. code-block:: yaml

            customPlaybooks:
              - triggers:
                - on_helm_release_uninstall:
                    names: ["demo-app"] # optional
                    namespace: "default" # optional
                actions:
                  - helm_status_enricher: {}

    .. image:: /images/helm-release-uninstalled.png
      :width: 1000
      :align: center
