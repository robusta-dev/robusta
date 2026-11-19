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

You can also combine static text with placeholders (e.g. ``"Bearer {{ env.TOKEN }}"``)
or reference multiple environment variables in the same field
(e.g. ``"{{ env.USER }}:{{ env.PASSWORD }}"``).

.. note::

   ``{{ env.X }}`` substitution only happens inside Robusta's configuration
   (``sinks``, ``globalConfig``, ``customPlaybooks``, ``playbookRepos``). The
   environment variable still needs to actually exist inside the pod that reads
   that config — see :ref:`Runner vs. HolmesGPT pods` below.

Injecting Many Keys at Once with ``additional_env_froms``
-----------------------------------------------------------

If you have a Secret (or ConfigMap) with multiple keys you want to expose to the
runner, ``runner.additional_env_froms`` is often less verbose than listing each
key under ``additional_env_vars``:

.. code-block:: yaml

  runner:
    additional_env_froms:
      - secretRef:
          name: my-robusta-secrets

Every key in ``my-robusta-secrets`` becomes an environment variable on the runner
pod (key name = env var name), which you can then reference with
``{{ env.KEY_NAME }}``.

.. _Runner vs. HolmesGPT pods:

Runner vs. HolmesGPT Pods
--------------------------------------------------

Robusta runs as multiple pods. An environment variable defined under ``runner.additional_env_vars``
is **only** available to the runner; one defined under ``holmes.additionalEnvVars`` is **only**
available to the HolmesGPT pod. If a value (e.g. an API key) is consumed by both, you must add
the env var to **both** blocks — they do not share environment.

A common pitfall: a secret referenced inside ``globalConfig`` is read by the runner, so it
needs to be in ``runner.additional_env_vars``. The same secret used by HolmesGPT must
**also** be added to ``holmes.additionalEnvVars``.

Secrets for HolmesGPT Add-Ons
--------------------------------------------------

The ``holmes.additionalEnvVars`` block only injects env vars into the main HolmesGPT pod.
HolmesGPT also ships several optional sub-deployments that have their own
``additionalEnvVars`` arrays:

- ``holmes.operator.additionalEnvVars`` — for the HolmesGPT operator
- ``holmes.mcpAddons.aws.additionalEnvVars`` — for the AWS MCP add-on
- ``holmes.mcpAddons.azure.additionalEnvVars`` — for the Azure MCP add-on

If you enable any of those add-ons and need to pass them a secret, add it under the
matching block — values placed only in ``holmes.additionalEnvVars`` will not reach
the add-on pods.

.. _Reading the Robusta UI Token from a secret in HolmesGPT:

Using an Existing Secret for the Robusta UI Token
--------------------------------------------------------

If you store the Robusta UI token in a Kubernetes secret (instead of directly in Helm values), you need to pass it to HolmesGPT:

.. code-block:: yaml

    holmes:
      additionalEnvVars:
      - name: ROBUSTA_UI_TOKEN
        valueFrom:
          secretKeyRef:
            name: my-robusta-secrets  # Your existing secret
            key: ui-token             # Your existing key
