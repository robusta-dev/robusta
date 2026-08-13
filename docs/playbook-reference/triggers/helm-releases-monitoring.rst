Helm Releases Monitoring
#############################

Robusta can monitor your Helm releases and notify you about updates or problems. For example:

* Get notified in Slack when a Helm release fails
* Get notified in MSTeams if a Helm release is pending for more than X seconds
* Send details on your Helm history to external tools

…and more

Prerequisites
---------------
There are two prerequisites for using Helm triggers:

* The :ref:`Robusta UI` sink must be enabled
* ``monitorHelmReleases: true`` must be set in Robusta's Helm values

Supported release storage types
--------------------------------

Robusta discovers Helm releases by reading the release state that Helm itself stores in the cluster.
Only the following storage backend is supported:

.. list-table::
   :header-rows: 1
   :widths: 25 30 45

   * - Helm storage driver
     - Kubernetes object read
     - Supported
   * - ``secret`` (Helm v3 default)
     - ``Secret`` of type ``helm.sh/release.v1``, labeled ``owner=helm``
     - ✅ Yes
   * - ``configmap``
     - ``ConfigMap`` with release payload
     - ❌ No
   * - ``sql``
     - External SQL database
     - ❌ No
   * - Helm v2 (Tiller)
     - ``ConfigMap`` in ``kube-system``
     - ❌ No

When listing secrets, Robusta always applies the label selector ``owner=helm`` and only decodes the
``release`` payload of matching secrets — the contents of other secrets are never read or sent anywhere.

Required permissions
---------------------

Setting ``monitorHelmReleases: true`` adds ``get``, ``list`` and ``watch`` on ``secrets`` to the
runner's ``ClusterRole``. This grant is cluster-wide, so releases in **all namespaces** are monitored.

This is a Kubernetes RBAC limitation: RBAC rules cannot filter by secret ``type`` or by label, so it is
not possible to grant access only to ``helm.sh/release.v1`` secrets. Although Robusta itself only reads
Helm release secrets (see above), the permission technically allows reading any secret in the cluster.

If this grant does not fit your security requirements, you can:

* Keep ``monitorHelmReleases: false`` (the default). No secret read permission is granted, and the
  runner sets ``DISABLE_HELM_MONITORING`` so it never attempts to list secrets.
* Replace the runner's RBAC rules entirely with ``runner.overrideClusterRoles`` in Robusta's Helm
  values, and manage the secret permissions yourself.

Triggers
-----------

The following triggers are available:

.. _on_helm_release_unhealthy:

.. details:: on_helm_release_unhealthy


    ``on_helm_release_unhealthy`` triggers when a Helm release remains unhealthy for over ``duration`` seconds.  Unhealthy states are: ``uninstalling``, ``pending-install``, ``pending-upgrade``, and ``pending-rollback``.


    **Available options**:

    * ``rate_limit``: Limit firing to once every `rate_limit` seconds.
    * ``names``: List of Helm releases for this trigger to monitor. Leaving this field empty monitors all releases in the namespace. Optional.
    * ``namespace``: The Kubernetes namespace for this trigger to monitor. Leaving this field empty monitors all namespaces in the cluster. Optional.
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

    ``on_helm_release_fail`` is triggered when a Helm release enters a ``failed`` state. This is a one-time trigger, meaning that it only fires once when the release fails.

    **Available options**:

    * ``names``: List of Helm releases for this trigger to monitor. Leaving this field empty monitors all releases in the namespace. Optional.
    * ``namespace``: The Kubernetes namespace for this trigger to monitor. Leaving this field empty monitors all namespaces in the cluster. Optional.

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

    The ``on_helm_release_deploy`` is triggered when a Helm release enters a ``deployed`` state. This is a one-time trigger, meaning that it only fires once when the release is successfully deployed.

    **Available options**:

    * ``names``: List of Helm releases for this trigger to monitor. Leaving this field empty monitors all releases in the namespace. Optional.
    * ``namespace``: The Kubernetes namespace for this trigger to monitor. Leaving this field empty monitors all namespaces in the cluster. Optional.

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
