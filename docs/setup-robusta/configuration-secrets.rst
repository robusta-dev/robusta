Managing Secrets
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Some configuration values are considered secrets and cannot be saved in plain text format.

We recommend using `SealedSecrets <https://github.com/bitnami-labs/sealed-secrets>`_ or another secret management
system for Kubernetes.

As an alternative, Robusta can pull secret values from Kubernetes secrets.

Pulling Values from Kubernetes Secrets
--------------------------------------------------

Robusta supports loading sensitive values from Kubernetes Secrets using environment variables.
This works for most configuration values, including sinks, globalConfig, and custom_playbooks.

Step-by-Step Example: Inject a Grafana API Key
==================================================
Let's walk through an example where a Grafana API key is stored in a Kubernetes Secret and used in Robusta's configuration.

**1. Create the Kubernetes Secret**

First, create a Secret named ``my-robusta-secrets`` with the key ``secret_grafana_key``:

.. code-block:: bash

  kubectl create secret generic my-robusta-secrets \
    --from-literal=secret_grafana_key=YOUR_GRAFANA_API_KEY

**2. Reference the Secret as an Environment Variable in Helm**

Add the following to your Helm values (generated_values.yaml):


.. code-block:: yaml

  runner:
    additional_env_vars:
      - name: GRAFANA_KEY
        valueFrom:
          secretKeyRef:
            name: my-robusta-secrets
            key: secret_grafana_key

  # if you're configuring a secret for HolmesGPT it would be:
  holmes:
    additionalEnvVars:
      - name: GRAFANA_KEY
        valueFrom:
          secretKeyRef:
            name: my-robusta-secrets
            key: secret_grafana_key

**3. Use the Environment Variable in Robusta Config**

You can now reference the environment variable elsewhere in your configuration using the ``{{ env.VARIABLE_NAME }}`` syntax:

.. code-block:: yaml


  globalConfig:
    grafana_api_key: "{{ env.GRAFANA_KEY }}"
    grafana_url: http://grafana.namespace.svc

This setup keeps sensitive values out of your Helm files and version control, while still allowing them to be dynamically injected at runtime.

.. _Loading Robusta credentials from secrets:

Loading ``account_id``, ``signing_key``, and the UI token from secrets
------------------------------------------------------------------------------

After signing up, the Robusta install wizard generates a ``generated_values.yaml`` file with three
sensitive credentials that are normally written in plain text:

* ``globalConfig.account_id`` — your Robusta account ID
* ``globalConfig.signing_key`` — used to verify signatures on data sent to the runner
* ``sinksConfig[].robusta_sink.token`` — the token the Robusta UI sink uses to send findings to the backend; HolmesGPT also uses this token to talk to the backend

To load these from a Kubernetes Secret (or an external secret manager that injects values as env vars,
e.g. SealedSecrets, External Secrets, Vault, Azure Key Vault), use the steps below.

.. admonition:: Where each value is needed
    :class: note

    * ``account_id`` and ``signing_key`` are read by the **runner** (via ``globalConfig``).
    * The UI / sink token is read by the **runner** (via ``sinksConfig`` for the ``robusta_sink``) **and** by **HolmesGPT** (to authenticate to the Robusta backend). The same value must therefore be available as an env var on both pods.

**1. Create a Kubernetes Secret with all three values**

.. code-block:: bash

  kubectl create secret generic my-robusta-secrets \
    --from-literal=account-id=YOUR_ACCOUNT_ID \
    --from-literal=signing-key=YOUR_SIGNING_KEY \
    --from-literal=ui-token=YOUR_UI_TOKEN

**2. Reference the secret on both the runner and Holmes**

The token needs to be exposed as an env var on **both** the runner pod and the Holmes pod. The
``account_id`` and ``signing_key`` only need to be exposed on the runner.

.. code-block:: yaml

    runner:
      additional_env_vars:
        - name: ACCOUNT_ID
          valueFrom:
            secretKeyRef:
              name: my-robusta-secrets
              key: account-id
        - name: SIGNING_KEY
          valueFrom:
            secretKeyRef:
              name: my-robusta-secrets
              key: signing-key
        - name: ROBUSTA_UI_TOKEN
          valueFrom:
            secretKeyRef:
              name: my-robusta-secrets
              key: ui-token

    # Only required if HolmesGPT is enabled (enableHolmesGPT: true)
    holmes:
      additionalEnvVars:
        - name: ROBUSTA_UI_TOKEN
          valueFrom:
            secretKeyRef:
              name: my-robusta-secrets
              key: ui-token

**3. Reference the env vars from globalConfig and sinksConfig**

.. code-block:: yaml

    globalConfig:
      account_id: "{{ env.ACCOUNT_ID }}"
      signing_key: "{{ env.SIGNING_KEY }}"

    sinksConfig:
      - robusta_sink:
          name: robusta_ui_sink
          token: "{{ env.ROBUSTA_UI_TOKEN }}"

After applying these values, the runner and Holmes both pick up the credentials from the secret
without storing them in plain text anywhere in your Helm values or Git repository.

.. admonition:: Using an external secret manager
    :class: note

    Any system that injects secrets as environment variables on the pod will work the same way —
    just use that system's mechanism in place of ``secretKeyRef``. For example, with Azure Key Vault
    you might write ``value: ui-token@azurekeyvault`` in ``additional_env_vars`` / ``additionalEnvVars``,
    and the rest of the config (``globalConfig``, ``sinksConfig``) stays identical.

.. admonition:: Non-default API regions (e.g. EU)
    :class: tip

    If your account is hosted in a non-default region, you also need to point the runner and Holmes at
    the correct endpoints. Add these to ``runner.additional_env_vars`` and ``holmes.additionalEnvVars``:

    .. code-block:: yaml

        runner:
          additional_env_vars:
            - name: ROBUSTA_API_ENDPOINT
              value: https://api.eu.robusta.dev
            - name: ROBUSTA_UI_DOMAIN
              value: https://platform.eu.robusta.dev
            - name: ROBUSTA_TELEMETRY_ENDPOINT
              value: https://api.eu.robusta.dev/telemetry
            - name: RELAY_EXTERNAL_ACTIONS_URL
              value: https://api.eu.robusta.dev/integrations/generic/actions
            - name: WEBSOCKET_RELAY_ADDRESS
              value: wss://relay.eu.robusta.dev

        holmes:
          additionalEnvVars:
            - name: ROBUSTA_AI
              value: "true"
            - name: ROBUSTA_API_ENDPOINT
              value: https://api.eu.robusta.dev
            - name: ROBUSTA_UI_DOMAIN
              value: https://platform.eu.robusta.dev

    See :ref:`Robusta env var reference` for the full list.

.. _Reading the Robusta UI Token from a secret in HolmesGPT:

Using an Existing Secret for the Robusta UI Token (HolmesGPT only)
---------------------------------------------------------------------------

If you only need to inject the UI token into HolmesGPT (for example, the runner already has it via a
different mechanism), use the snippet below. For the full setup that also covers ``account_id``,
``signing_key``, and the sink token on the runner, see
:ref:`Loading Robusta credentials from secrets` above.

.. code-block:: yaml

    holmes:
      additionalEnvVars:
      - name: ROBUSTA_UI_TOKEN
        valueFrom:
          secretKeyRef:
            name: my-robusta-secrets  # Your existing secret
            key: ui-token             # Your existing key
