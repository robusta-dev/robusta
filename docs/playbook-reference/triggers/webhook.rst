Webhooks
#########################

External webhooks
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

From outside the cluster you can trigger manual playbook actions if you've enabled the Robusta-relay. For security reasons,
this requires the runner's signing key.

See the :ref:`Elasticsearch` integration for an example.

Prerequisites
--------------
1. The Robusta-relay must be enabled so that it can route webhooks to the appropriate Robusta runner
2. The following variables must be defined in your Helm values file:

.. code-block:: yaml

    globalConfig:
      account_id: ""       # your official Robusta account_id
      signing_key: ""      # a secret key used to verify that webhook callers are allowed to trigger playbooks
