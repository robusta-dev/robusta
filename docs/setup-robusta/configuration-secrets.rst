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

Sharing Prometheus Auth Between Runner and Holmes
==================================================

When using an external Prometheus with authentication and HolmesGPT enabled, you need to configure the same credentials in two places:

- ``globalConfig.prometheus_auth`` — used by the Robusta runner
- ``holmes.toolsets.prometheus/metrics.config.headers.Authorization`` — used by HolmesGPT

To avoid duplicating secrets in plain text, store the credential once in a Kubernetes Secret and reference it from both components:

**1. Create the Kubernetes Secret**

.. code-block:: bash

  kubectl create secret generic prometheus-auth-secret -n robusta \
    --from-literal=auth="Basic dXNlcm5hbWU6cGFzc3dvcmQ="

**2. Reference it from both the runner and Holmes**

.. code-block:: yaml

  runner:
    additional_env_vars:
      - name: PROMETHEUS_AUTH
        valueFrom:
          secretKeyRef:
            name: prometheus-auth-secret
            key: auth

  holmes:
    additionalEnvVars:
      - name: PROMETHEUS_AUTH
        valueFrom:
          secretKeyRef:
            name: prometheus-auth-secret
            key: auth

**3. Use the environment variable in both configs**

.. code-block:: yaml

  globalConfig:
    prometheus_url: "https://prometheus.example.com:9090"
    prometheus_auth: "{{ env.PROMETHEUS_AUTH }}"

  holmes:
    toolsets:
      prometheus/metrics:
        enabled: true
        config:
          prometheus_url: "https://prometheus.example.com:9090"
          headers:
            Authorization: "{{ env.PROMETHEUS_AUTH }}"

This way the secret is stored once in Kubernetes and injected into both the runner and Holmes at runtime.

.. note::

   Both the runner and Holmes need the environment variable injected separately because they run as separate deployments. The ``runner.additional_env_vars`` injects into the runner pod, while ``holmes.additionalEnvVars`` injects into the Holmes pod.
