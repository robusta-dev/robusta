VictoriaMetrics
*************************


General Instructions
======================
To configure VictoriaMetrics to send alerts to Robusta, add two settings to AlertManager:

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

Related Robusta Settings
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Below are additional Robusta settings related to VictoriaMetrics and AlertManager, and Grafana.

Setting up a custom VictoriaMetrics and AlertManager, and Grafana
==========================================================

If you followed the instructions on this page, VictoriaMetrics and AlertManager will know about Robusta, but Robusta might not know about them!

For certain features, Robusta needs to reach out to VictoriaMetrics and pull in extra information. This must
be configured **in addition** to updating AlertManager's configuration.

That said, most users won't need to set this up. Robusta can usually figure out where VictoriaMetrics and
other services are located. If the auto-discovery isn't working, you'll configure it manually.

Add the following to ``generated_values.yaml`` and :ref:`update Robusta <Simple Upgrade>`.

.. code-block:: yaml

  # this line should already exist
  globalConfig:
      # add the lines below
      alertmanager_url: ""
      grafana_url: ""
      victoriaMetrics_url: "http://VICTORIAMETRICS_SERVICE_NAME.monitoring.svc.cluster.local:9090"

Additional Authentication Headers
---------------------------------
If your VictoriaMetrics needs authentication, add the following to ``generated_values.yaml``:

.. code-block:: yaml

  globalConfig:
    prometheus_auth: Bearer <YOUR TOKEN> # or any other auth header

For AlertManager:

.. code-block:: yaml

    globalConfig:
      alertmanager_auth: Basic <USER:PASSWORD base64-encoded> # or any other auth header

.. note::

      If both a Grafana API key and AlertManager auth are defined, Robusta will use the Grafana API key


Alerts silencing
=================

Robusta lets you silence alerts directly from your notification channels (sinks). Robusta will try to automatically find
an AlertManager running in your cluster and use it to create silences.

If Robusta can't find your AlertManager, :ref:`tell it where to find it <Setting up a custom VictoriaMetrics and AlertManager, and Grafana>`.

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
