Managing Secrets in Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Some of the configuration values are considered secrets, and cannot be saved in plain text format.
We recommend using `SealedSecrets <https://github.com/bitnami-labs/sealed-secrets>`_
or one of the other secret management system for Kubernetes, to encrypt the secret values.

As an alternative, we can pull secret values from Kubernetes secrets.

First, define an environment variable that is taken from a Kubernetes secret.

In your ``generated_values.yaml`` file add:

.. code-block:: yaml

   runner:
     additional_env_vars:
     - name: GRAFANA_KEY
       valueFrom:
         secretKeyRef:
           name: my-robusta-secrets
           key: secret_grafana_key


Next, define that the value should be pulled from an environment variable by using the special {{ env.VARIABLE }} syntax:

.. code-block:: yaml

   globalConfig:
     grafana_api_key: "{{ env.GRAFANA_KEY }}"
     grafana_url: http://grafana.namespace.svc

Finally, create a Kubernetes secret named ``my-robusta-secrets``, and in it ``secret_grafana_key`` with your grafana api key.

Values can be taken from environment variables in:

* global config
* playbooks action parameters
* sinks configuration


