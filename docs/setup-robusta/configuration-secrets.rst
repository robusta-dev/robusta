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

  # if you're configuring a secret for HolmesGPT use this instead
  #holmes:
  #  additionalEnvVars:
  #  - name: ROBUSTA_AI
  #    value: "true"

**3. Use the Environment Variable in Robusta Config**

You can now reference the environment variable elsewhere in your configuration using the ``{{ env.VARIABLE_NAME }}`` syntax:

.. code-block:: yaml


  globalConfig:
    grafana_api_key: "{{ env.GRAFANA_KEY }}"
    grafana_url: http://grafana.namespace.svc

This setup keeps sensitive values out of your Helm files and version control, while still allowing them to be dynamically injected at runtime.
