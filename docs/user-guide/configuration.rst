Configuration Guide
################################

Robusta is configured using Helm values. This page documents the important values.

All possible values can be found by running:

.. code-block:: yaml

    helm repo add robusta https://robusta-charts.storage.googleapis.com && helm repo update
    helm show values robusta/robusta

Do not use the ``values.yaml`` file in the GitHub repo. It has some empty placeholders which are replaced during
our release process.


Defining playbooks
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Playbooks are defined using the ``customPlaybooks`` Helm value.

Every playbooks has three parts: triggers, actions, and sinks. See the :ref:`Track Kubernetes Changes` tutorial for
a walkthrough.

.. code-block:: yaml

    customPlaybooks:
    - triggers:
      - on_deployment_update:
      actions:
      - resource_babysitter:
          fields_to_monitor: ["status.conditions"]
      sinks:
      - "main_slack_sink"

Configuring triggers
----------------------
Triggers define when a playbook runs:

.. code-block:: yaml
    :emphasize-lines: 3-4

    customPlaybooks:
      - triggers:
          - on_deployment_update:
              name_prefix: MyApp
        actions:
          - resource_babysitter:
              fields_to_monitor: ["status.conditions"]
        sinks:
          - "main_slack_sink"

.. note::

    In the yaml, ``triggers`` is an array, but currently it must contain exactly one entry.

Most triggers support extra filters like ``name_prefix`` which further restricts the trigger.

Multiple playbook instances
-----------------------------------

You can enable a playbook multiple times with different configurations:

.. code-block:: yaml

    customPlaybooks:
    - triggers:
      - on_deployment_update:
          name_prefix: MyApp
      actions:
      - add_deployment_lines_to_grafana:
          grafana_api_key: grafana_key_goes_here
          grafana_dashboard_uid: id_for_dashboard1
          grafana_url: http://grafana.namespace.svc
      sinks:
      - "main_slack_sink"

    - triggers:
      - on_deployment_update:
          name_prefix: OtherApp
      actions:
      - add_deployment_lines_to_grafana:
          grafana_api_key: grafana_key_goes_here
          grafana_dashboard_uid: id_for_dashboard2
          grafana_url: http://grafana.namespace.svc
      sinks:
      - "main_slack_sink"

Global config
^^^^^^^^^^^^^^^^^^^^^^^^^^

In the previous example, ``grafana_api_key`` and ``grafana_url`` were defined multiple times with the same value.

To avoid repeating yourself, you can define parameters globally for all playbooks. These parameters will be applied to
any action or trigger which expects a parameter with the same name.

.. code-block:: yaml

   globalConfig:
     cluster_name: "my-staging-cluster"
     grafana_api_key: "grafana_key_goes_here"
     grafana_url: http://grafana.namespace.svc

    customPlaybooks:
    - triggers:
      - on_deployment_update:
          name_prefix: MyApp
      actions:
      - add_deployment_lines_to_grafana:
          grafana_dashboard_uid: id_for_dashboard1
      sinks:
      - "main_slack_sink"

    - triggers:
      - on_deployment_update:
          name_prefix: OtherApp
      actions:
      - add_deployment_lines_to_grafana:
          grafana_dashboard_uid: id_for_dashboard2
      sinks:
      - "main_slack_sink"


Mandatory global config
^^^^^^^^^^^^^^^^^^^^^^^^^^

Robusta expects several ``globalConfig`` parameters with specific names:

cluster_name
    Unique for each cluster in your organization. Cluster Name be human-readable and need not be secret

account_id
    Keep secret! The Account ID uniquely identifies your cluster with Robusta cloud (if enabled). Should never be the
    same for different organizations. Together, ``cluster_name`` and ``account_id`` uniquely identify every cluster
    running Robusta in the world

signing_key
    Keep secret! The Signing Key is used to authenticate requests to run playbooks from outside the cluster (if enabled).

These values are generated automatically when setting up Robusta with the CLI. If you install Robusta on additional
clusters, make sure you change ``cluster_name`` accordingly. The other values should remain the same.

If you need to generate the secret values yourself, use cryptographically secure strings with at least 128 bits of
randomness.

Defining additional sinks
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Here is a full example showing how to configure all possible sinks:

.. code-block:: yaml

    sinksConfig:
    - slack_sink:
        name: main_slack_sink
        slack_channel: channel-name
        api_key: secret-key    # generated with `robusta integrations slack`
    - robusta_sink:
        name: robusta_ui_sink
        token: secret-api-key  # generated with `robusta gen-config`
    - ms_teams_sink:
        name: main_ms_teams_sink
        webhook_url: teams channel incoming webhook  # configured using teams channel connectors
    - kafka_sink:
        name: kafka_sink
        kafka_url: "localhost:9092"
        topic: "robusta-playbooks"
        default: false
    - datadog_sink:
        name: datadog_sink
        api_key: "datadog api key"
        default: false
    - opsgenie_sink:
        name: ops_genie_ui_sink
        api_key: OpsGenie integration API key  # configured from OpsGenie team integration
        teams:
        - "noc"
        - "sre"
        tags:
        - "prod a"

Configuration secrets
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Some of the configuration values are considered secrets, and cannot be saved in plain text format.
We recommend using `SealedSecrets <https://github.com/bitnami-labs/sealed-secrets>`_
or one of the other secret management system for Kubernetes, to encrypt the secret values.

As an alternative, we can pull secret values from Kubernetes secrets.

First, define an environment variable that is taken from a Kubernetes secret.

In your ``values.yaml`` file add:

.. code-block:: yaml

   runner:
     additional_env_vars: |-
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


Loading additional playbooks
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Playbook actions are loaded into Robusta using the ``playbookRepos`` Helm value.

Robusta has a set of builtin playbooks.

You can load extra playbook actions from git repositories:

.. code-block:: yaml

    playbookRepos:
      # we're adding the robusta chaos-engineering playbooks here
      my_extra_playbooks:
        url: "git@github.com:robusta-dev/robusta-chaos.git"
        key: |-
          -----BEGIN OPENSSH PRIVATE KEY-----
          ewfrcfsfvC1rZXktdjEAAAAABG5vb.....
          -----END OPENSSH PRIVATE KEY-----


The ``key`` should contain a deployment key, with ``read`` access. It isn't necessary for public repositories.

.. note::

    Robusta does not watch for changes on git repositories. Playbooks are loaded from the repository when the server
    starts or the configuration changes, or by running manual reload: ``robusta playbooks reload``

Embedded Prometheus Stack
^^^^^^^^^^^^^^^^^^^^^^^^^

Robusta can optionally install an embedded Prometheus stack with pre-configured alerts. Our goal is to provide defaults
that are fine-tuned for low-noise and out-of-the-box integration with Robusta playbooks.

This feature is disable by default. If you would like to enable it then set:

.. code-block:: yaml

    enablePrometheusStack: true

We recommend you enable this if haven't yet installed Prometheus on your cluster.

The alerts are based on excellent work already done by the kube-prometheus-stack project which itself takes
alerts from the kubernetes-mixin project.

Our alerting will likely diverge more over time as we take advantage of more Robusta features.