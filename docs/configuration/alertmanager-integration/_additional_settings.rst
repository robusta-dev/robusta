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
-------------------
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
------------------------

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