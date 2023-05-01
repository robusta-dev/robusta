Helm Releases Monitoring
#############################

Robusta is capable of monitoring your Helm releases and keeping you informed about their status. It can send you notifications when a release fails, is pending for more than x seconds, or gets deployed successfully, among other things.

Prerequisites
---------------
Robusta UI Sink must be connected to Robusta. Refer to :ref:`Robusta UI`.

Triggers
-----------

The following triggers are available:

.. _on_helm_release_data:

.. details:: on_helm_release_data


    The ``on_helm_release_data`` event is triggered whenever there is a change in the Helm release.

    * ``status``: A list of status in a helm release. Possible values: ``failed``, ``deployed``, ``uninstalled``, ``superseded``, ``uninstalling``, ``pending-install``, ``pending-upgrade``, ``pending-rollback`` and ``unknown``
    * ``names``: A list of Helm release names that this trigger will monitor. If you leave this field empty, the trigger will monitor all release names specified in the namespace. This field is optional.
    * ``namespace``: This field specifies the namespace that the trigger will monitor. If you leave this field empty, the trigger will monitor across all namespaces. This field is optional.
    * ``for_sec``: This field specifies the threshold time, in seconds, before the trigger could be initiated, and the release status should continue to stay within this threshold time before the trigger is initiated. This field is optional.
    * ``rate_limit``: Limit firing to once every `rate_limit` seconds. This field is optional.

    .. admonition:: Example

        .. code-block:: yaml

            customPlaybooks:
              - actions:
                - create_helm_status_notification:
                    message: "Helm release failed" # optional
                triggers:
                  - on_helm_release_data:
                      status: ["failed", "unknown"]
                      names: ["demo-app"] # optional
                      namespace: "default" # optional
                      rate_limit: 900 # optional
        .. code-block:: yaml

            customPlaybooks:
              - actions:
                - create_helm_status_notification:
                    message: "Helm release is pending" # optional
                triggers:
                  - on_helm_release_data:
                      status: ["pending-install", "pending-rollback"]
                      names: ["demo-app", "my-app"] # optional
                      namespace: "default" # optional
                      for_sec: 900 # optional
                      rate_limit: 900 # optional

        ``create_helm_status_notification`` supports the following parameters:
            ``message``: Custom message for the action event. This field is optional.
