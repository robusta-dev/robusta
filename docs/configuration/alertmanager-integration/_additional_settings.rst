Additional Authentication Headers
=================================
If Prometheus requires authentication, add the following to ``generated_values.yaml``:

.. code-block:: yaml

  globalConfig:
    prometheus_auth: Bearer <YOUR TOKEN> # Replace <YOUR TOKEN> with your actual token or use any other auth header as needed

AlertManager authentication, add the following to ``generated_values.yaml``.

.. code-block:: yaml

    globalConfig:
      alertmanager_auth: Basic <USER:PASSWORD base64-encoded> # Replace <USER:PASSWORD base64-encoded> with your actual credentials, base64-encoded, or use any other auth header as needed

.. note::

      If both a Grafana API key and AlertManager auth are defined, Robusta will use the Grafana API key

SSL Verification
===================
By default, Robusta does not verify the SSL certificate of the Prometheus server. To enable SSL verification, add the following to ``generated_values.yaml``:

.. code-block:: yaml

  runner:
    additional_env_vars:
    - name: PROMETHEUS_SSL_ENABLED
      value: "true"

To use a custom CA certificate, add the following to the ``generated_values.yaml`` file:

.. code-block:: yaml

  runner:
    certificate: "<YOUR BASE-64 ENCODED DATA>" # base64-encoded certificate value

Alerts silencing
=====================

Robusta enables the silencing of alerts directly from notification channels (sinks) Robusta attempts to find an AlertManager instance running in your cluster automatically and uses it to create silences.

If Robusta can't locate the AlertManager, a pull integration must be configured.

.. Grafana AlertManager
.. =====================
.. If you're using the AlertManager that's embedded in Grafana, you need to modify one additional setting so Robusta can create silences. This is necessary because of minor API differences in the AlertManager embedded in Grafana.

.. Add the following configuration to the ``globalConfig`` section in your ``generated_values.yaml`` file:

.. .. admonition:: generated_values.yaml

..     .. code-block:: yaml

..         globalConfig:
..           grafana_api_key: <YOUR GRAFANA EDITOR API KEY>
..           alertmanager_flavor: grafana

..     .. note::

..       The Grafana API key must have the ``Editor`` role in order to create silences.
