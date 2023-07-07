Managing Secrets
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Some configuration values are considered secrets and cannot be saved in plain text format.

We recommend using `SealedSecrets <https://github.com/bitnami-labs/sealed-secrets>`_ or another secret management
system for Kubernetes.

As an alternative, Robusta can pull secret values from Kubernetes secrets.

Pulling Values from Kubernetes Secrets
--------------------------------------------------

Robusta can pull values from Kubernetes secrets for:

* Sink Configuration
* Global Config
* Action Parameters

To do so, first define an environment variable based on a Kubernetes secret. Add to Robusta's Helm values:

.. code-block:: yaml

   runner:
     additional_env_vars:
     - name: GRAFANA_KEY
       valueFrom:
         secretKeyRef:
           name: my-robusta-secrets
           key: secret_grafana_key


Then reference that environment variable in other Helm values using the special ``{{ env.VARIABLE }}`` syntax:

.. code-block:: yaml

   globalConfig:
     grafana_api_key: "{{ env.GRAFANA_KEY }}"
     grafana_url: http://grafana.namespace.svc

Finally, make sure the Kubernetes secret actually exists. In this example, create a Secret named ``my-robusta-secrets``
with a ``secret_grafana_key`` value inside.
