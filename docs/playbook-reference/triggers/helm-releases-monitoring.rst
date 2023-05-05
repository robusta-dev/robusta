Helm Releases Monitoring
#############################

Robusta can monitor your Helm releases, notify you about updates, and take actions in response. For example, you can:

* Get notified in Slack when a Helm release fails
* Get notified in MSTeams if a Helm release is pending for more than X seconds
* Send details on your Helm history to external tools

…and more

Prerequisites
---------------
Robusta UI Sink must be connected to Robusta. Refer to :ref:`Robusta UI`.

Triggers
-----------

The following triggers are available:

.. _on_helm_release_unhealthy:

.. details:: on_helm_release_unhealthy


    The ``on_helm_release_unhealthy`` event is triggered when a Helm release remains in an unhealthy state for a prolonged period. Specifically, this trigger is activated when the release is in one of the following states for more than X seconds (which can be set using the ``duration`` field): ``uninstalling``, ``pending-install``, ``pending-upgrade``, or ``pending-rollback``.

    **Available options**:

    * ``names``: A list of Helm release names that this trigger will monitor. If you leave this field empty, the trigger will monitor all release names specified in the namespace. This field is optional.
    * ``namespace``: This field specifies the namespace that the trigger will monitor. If you leave this field empty, the trigger will monitor across all namespaces. This field is optional.
    * ``duration``: This field specifies the threshold time, in seconds, before the trigger could be initiated, and the release status should continue to stay within this threshold time before the trigger is initiated. This field is optional.
    * ``rate_limit``: Limit firing to once every `rate_limit` seconds. This field is optional.

    .. admonition:: Example

        This example demonstrates how to set up a trigger that watches a Helm release for an unhealthy state. If the release remains in a transient state for more than 1200 seconds, the `on_helm_release_unhealthy` trigger is activated.

        .. code-block:: yaml

            customPlaybooks:
              - actions:
                - helm_status_notification:
                    message: "Helm release is in an unhealthy state" # optional
                triggers:
                  - on_helm_release_unhealthy:
                      names: ["demo-app"] # optional
                      namespace: "default" # optional
                      duration: 1200 # optional
                      rate_limit: 900 # optional

        ``helm_status_notification`` supports the following parameters:
            ``message``: Custom message for the action event. This field is optional.

    .. image:: /images/helm-release-unhealthy.png
      :width: 1000
      :align: center


.. _on_helm_release_fail:

.. details:: on_helm_release_fail

    The ``on_helm_release_fail`` event is triggered when a Helm release enters a ``failed`` state. This is a one-time trigger, meaning that it only fires once when the release fails.

    **Available options**:

    * ``names``: A list of Helm release names that this trigger will monitor. If you leave this field empty, the trigger will monitor all release names specified in the namespace. This field is optional.
    * ``namespace``: This field specifies the namespace that the trigger will monitor. If you leave this field empty, the trigger will monitor across all namespaces. This field is optional.

    .. admonition:: Example

        This example demonstrates how to set up a trigger that watches a Helm release for an ``failed`` state.

        .. code-block:: yaml

            customPlaybooks:
              - actions:
                - helm_status_notification:
                    message: "Helm release failed" # optional
                triggers:
                  - on_helm_release_fail:
                      names: ["demo-app"] # optional
                      namespace: "default" # optional

        ``helm_status_notification`` supports the following parameters:
        * ``message``: Custom message for the action event. This field is optional.

    .. image:: /images/helm-release-failed.png
      :width: 1000
      :align: center

.. _on_helm_release_deploy:

.. details:: on_helm_release_deploy

    The ``on_helm_release_deploy`` event is triggered when a Helm release enters a ``deployed`` state. This is a one-time trigger, meaning that it only fires once when the release is deployed.

    **Available options**:

    * ``names``: A list of Helm release names that this trigger will monitor. If you leave this field empty, the trigger will monitor all release names specified in the namespace. This field is optional.
    * ``namespace``: This field specifies the namespace that the trigger will monitor. If you leave this field empty, the trigger will monitor across all namespaces. This field is optional.

    .. admonition:: Example

        This example demonstrates how to set up a trigger that watches a Helm release for an ``deployed`` state.

        .. code-block:: yaml

            customPlaybooks:
              - actions:
                - helm_status_notification:
                    message: "Helm release is deployed" # optional
                triggers:
                  - on_helm_release_deploy:
                      names: ["demo-app"] # optional
                      namespace: "default" # optional

        ``helm_status_notification`` supports the following parameters:
            ``message``: Custom message for the action event. This field is optional.

    .. image:: /images/helm-release-deployed.png
      :width: 1000
      :align: center


.. _on_helm_release_uninstall:

.. details:: on_helm_release_uninstall

    The ``on_helm_release_uninstall`` event is triggered when a Helm release enters a ``uninstalled`` state. This is a one-time trigger, meaning that it only fires once when the release is uninstalled.

    **Available options**:

    * ``names``: A list of Helm release names that this trigger will monitor. If you leave this field empty, the trigger will monitor all release names specified in the namespace. This field is optional.
    * ``namespace``: This field specifies the namespace that the trigger will monitor. If you leave this field empty, the trigger will monitor across all namespaces. This field is optional.

    .. admonition:: Example

        This example demonstrates how to set up a trigger that watches a Helm release for an ``uninstalled`` state.

        .. code-block:: yaml

            customPlaybooks:
              - actions:
                - helm_status_notification:
                    message: "Helm release was uninstalled" # optional
                triggers:
                  - on_helm_release_uninstall:
                      names: ["demo-app"] # optional
                      namespace: "default" # optional

        ``helm_status_notification`` supports the following parameters:
            ``message``: Custom message for the action event. This field is optional.

    .. image:: /images/helm-release-uninstalled.png
      :width: 1000
      :align: center
