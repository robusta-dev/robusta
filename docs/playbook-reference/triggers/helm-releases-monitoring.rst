Helm Releases Monitoring
#############################

Robusta is capable of monitoring your Helm releases and keeping you informed about their status. It can send you notifications when a release fails, is pending for more than x seconds, or gets deployed successfully, among other things.

Triggers
-----------

The following triggers are available:

.. _on_helm_release_data:

.. details:: on_helm_release_data


    The ``on_helm_release_data`` event is triggered whenever there is a change in the Helm release.

    * ``status``: The status of a helm release. Possible values: ``failed``, ``deployed``, ``uninstalled``, ``superseded``, ``uninstalling``, ``pending-install``, ``pending-upgrade``, ``pending-rollback`` and ``unknown``
    * ``names``: A list of Helm release names that this trigger will monitor. If you leave this field empty, the trigger will monitor all release names specified in the namespace.
    * ``namespace``: This field specifies the namespace that the trigger will monitor. If you leave this field empty, the trigger will monitor across all namespaces.
    * ``for_sec``: This field specifies the threshold time, in seconds, before the trigger could be initiated, and the release status should continue to stay within this threshold time before the trigger is initiated.
    * ``rate_limit``: Limit firing to once every `rate_limit` seconds

    .. admonition:: Example

        Run

        .. code-block:: yaml

            customPlaybooks:
              - actions:
                - create_helm_status_notification:
                    message: "Helm release failed"
                triggers:
                  - on_helm_release_data:
                      status: "failed"
                      names: ["demo-app"] # optional
                      namespace: "default" # optional
                      rate_limit: 900 # optional
        .. code-block:: yaml

            customPlaybooks:
              - actions:
                - create_helm_status_notification:
                    message: "Helm release is pending"
                triggers:
                  - on_helm_release_data:
                      status: "pending-install"
                      names: ["demo-app"] # optional
                      namespace: "default" # optional
                      for_sec: 900 # optional
                      rate_limit: 900 # optional
