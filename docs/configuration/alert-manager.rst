Integrating AlertManager and Prometheus
****************************************

Sending Alerts to Robusta
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For Robusta to :ref:`improve Prometheus alerts<Enhanced Prometheus Alerts>`, Robusta has to first receive those alerts from AlertManager.

**If you installed Robusta's** :ref:`Embedded Prometheus Stack` **then no configuration is necessary.**

For other setups, read on!

General Instructions
======================
To configure Prometheus to send alerts to Robusta, add two settings to AlertManager:

1. A webhook receiver for Robusta
2. A route for the webhook receiver you added

Below is an example AlertManager configuration. Depending on your setup, the exact file to edit may vary. (See below.)

.. admonition:: AlertManager config for sending alerts to Robusta

    .. code-block:: yaml

        receivers:
          - name: 'robusta'
            webhook_configs:
              # the following line assumes that Robusta was installed in the `default` namespace.
              # if you installed Robusta in a different namespace, replace `default` with the correct namespace
              # likewise, if you named your Helm release ``robert`` then replace ``robusta`` with ``robert``
              - url: 'http://robusta-runner.default.svc.cluster.local/api/alerts'
                send_resolved: true

        route:
          routes:
            - receiver: 'robusta'
              matchers:
                - severity =~ "info|warn|error|critical"
              repeat_interval: 4h
              continue: true

.. admonition:: Common Mistakes

    1. Make sure the Robusta ``route`` is the first ``route`` defined. If it isn't the first route, it might not receive alerts. When a ``route`` is matched, the alert will not be sent to following routes, unless the ``route`` is configured with ``continue: true``.
    2. Tweak the settings accordingly if:
        * You installed Robusta in a namespace other than ``default``
        * You named Robusta's Helm release something other than ``robusta``

After you configure AlertManager, you can test it works properly, by creating a demo alert:

.. code-block:: bash

    robusta demo-alert

Within a few minutes, you should see the demo alert in the Robusta UI, Slack, and any other sinks you configured.

.. admonition:: Why do I see a banner in the UI that "Alerts won't show up"?
    :class: warning

    This notification is displayed until AlertManager sends the first alert to Robusta.

Specific Instructions
======================

Here are instructions for configuring AlertManager in specific setups. Don't see your setup? Just follow the
:ref:`General Instructions` above.

kube-prometheus-stack and Prometheus Operator
------------------------------------------------

If you installed kube-prometheus-stack or the Prometheus Operator **by yourself** (not via Robusta) then tell
AlertManager about Robusta using a `Kubernetes Secret <https://github.com/prometheus-operator/prometheus-operator/blob/main/Documentation/user-guides/alerting.md#managing-alertmanager-configuration>`_.
The Prometheus Operator will pass this secret to AlertManager, which will then push alerts to Robusta by webhook.

To configure the secret, copy the configuration :ref:`here <General Instructions>` and place it in the appropriate secret.

.. admonition:: Why use a secret instead of editing AlertManagerConfig?

    In theory, you can configure an AlertmanagerConfig instead of using a secret. However, this is **not** recommended.
    It `will only forward alerts from one namespace <https://github.com/prometheus-operator/prometheus-operator/issues/3750>`_.

Out-of-cluster Prometheus Installations
-----------------------------------------

If AlertManager is located outside of your Kubernetes cluster then a few more steps are necessary:

1. Enable two-way interactivity in :ref:`Robusta's configuration <Configuration Overview>` by setting ``disableCloudRouting: false``
2. Make sure that your alerts contain a label named ``cluster_name`` which matches the :ref:`cluster_name defined in Robusta's configuration <Global Config>`. This is necessary so that the Robusta cloud knows which cluster to forward events to.
3. Configure AlertManager as follows:

.. admonition:: alertmanager.yaml

    .. code-block:: yaml

        receivers:
          - name: 'robusta'
            webhook_configs:
              - url: 'https://api.robusta.dev/integrations/generic/alertmanager'
                http_config:
                  authorization:
                    # Replace <TOKEN> with a string in the format `<ACCOUNT_ID> <SIGNING_KEY>`
                    credentials: <TOKEN>
                send_resolved: true

        route:
          routes:
          - receiver: 'robusta'
            matchers:
              - severity =~ "info|warn|error|critical"
            repeat_interval: 4h
            continue: true

Related Robusta Settings
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Below are additional Robusta settings related to Prometheus, AlertManager, and Grafana.

Setting up a custom Prometheus, AlertManager, and Grafana
==========================================================

If you followed the instructions on this page, Prometheus and AlertManager will know about Robusta, but Robusta might not know about them!

For certain features, Robusta needs to reach out to Prometheus and pull in extra information. This must
be configured **in addition** to updating AlertManager's configuration.

That said, most users won't need to set this up. Robusta can usually figure out where Prometheus and
other services are located. If the auto-discovery isn't working, you'll configure it manually.

Add the following to ``generated_values.yaml`` and :ref:`update Robusta <Simple Upgrade>`.

.. code-block:: yaml

  # this line should already exist
  globalConfig:
      # add the lines below
      alertmanager_url: ""
      grafana_url: ""
      prometheus_url: "http://PROMETHEUS_SERVICE_NAME.monitoring.svc.cluster.local:9090"

Additional Authentication Headers
---------------------------------
If your Prometheus needs authentication, add the following to ``generated_values.yaml``:

.. code-block:: yaml

  globalConfig:
    prometheus_auth: Bearer <YOUR TOKEN> # or any other auth header

For AlertManager:

.. code-block:: yaml

    globalConfig:
      alertmanager_auth: Basic <USER:PASSWORD base64-encoded> # or any other auth header

.. note::

      If both a Grafana API key and AlertManager auth are defined, Robusta will use the Grafana API key

SSL Verification
----------------
By default, Robusta does not verify the SSL certificate of the Prometheus server. To enable SSL verification, add the following to ``generated_values.yaml``:

.. code-block:: yaml

  runner:
    additional_env_vars:
    - name: PROMETHEUS_SSL_ENABLED
      value: "true"

To add a custom CA certificate, add the following as well:

.. code-block:: yaml

  runner:
    certificate: "<YOUR BASE-64 ENCODED DATA>" # base64-encoded certificate value

Alerts silencing
=================

Robusta lets you silence alerts directly from your notification channels (sinks). Robusta will try to automatically find
an AlertManager running in your cluster and use it to create silences.

If Robusta can't find your AlertManager, :ref:`tell it where to find it <Setting up a custom Prometheus, AlertManager, and Grafana>`.

Grafana AlertManager
----------------------
If you use the AlertManager embedded in Grafana, change one more setting for Robusta to create silences.

Add the following configuration to the ``globalConfig`` section in your ``generated_values.yaml`` file:

.. admonition:: generated_values.yaml

    .. code-block:: yaml

        globalConfig:
          grafana_api_key: <YOUR GRAFANA EDITOR API KEY>
          alertmanager_flavor: grafana

    .. note::

      The Grafana api key must have ``Editor`` permission in order to create silences

This is necessary due to minor API changes in the embedded AlertManager that Grafana runs.
