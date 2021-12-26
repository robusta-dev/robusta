Configuration Guide
################################

Robusta is configured using Helm values. All possible values can be found in
`values.yaml <https://github.com/robusta-dev/robusta/blob/master/helm/robusta/values.yaml>`_

This page documents the important values.


Defining playbooks
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Playbooks are defined using the ``customPlaybooks`` Helm value:

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
In the yaml, ``triggers`` is an array, but currently it must contain exactly one entry.

Most triggers support filters to further restrict when the playbook runs:

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

These filters are almost always optional. When left out, the filter matches everything.

Kubernetes triggers support ``name_prefix`` and ``namespace_prefix``

Prometheus triggers support filters like ``alert_name``

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

Robusta also expects several ``globalConfig`` parameters with specific names:

cluster_name
    Unique for each cluster in your organization. Can be human-readable and need not be secret

account_id
    Keep secret! Uniquely identifies your cluster with Robusta cloud (if enabled). Should never be the same for different
    organizations. Together, ``cluster_name`` and ``account_id`` uniquely identify every cluster running Robusta in the world

signing_key
    Keep secret! This is used to authenticate requests to run playbooks from outside the cluster (if enabled).

These values are generated automatically when setting up Robusta with the CLI. If you install Robusta on additional
clusters, make sure you change ``cluster_name`` accordingly. The other values should remain the same.

If you need to generate the secret values yourself, use cryptographically secure strings with at least 128 bits of
randomness.

Defining additional sinks
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. warning:: This section describes the internal Robusta ``active_playbooks.yaml`` file. This functionality is not yet exposed in the Helm chart's ``values.yaml``

To use sinks, first define the available named sinks in ``active_playbooks.yaml``.

.. code-block:: yaml

    sinks_config:
    - slack_sink:
        name: slack sink
        api_key: "api-key from running `robusta integrations slack`"
        slack_channel: channel1
        default: true

    - robusta_sink:
        name: robusta_ui_sink
        token: "signup for a token online"
        default: true

    - kafka_sink:
        name: kafka_sink
        kafka_url: "localhost:9092"
        topic: "robusta-playbooks"
        default: false

    - datadog_sink:
        name: datadog_sink
        api_key: "datadog api key"
        default: false

You can explicitly specify sinks per playbook, like above.

If you don't specify sinks for a playbook, the default sinks will be used.

Embedded Prometheus Stack
^^^^^^^^^^^^^^^^^^^^^^^^^

Robusta can optionally install an embedded Prometheus stack with pre-configured alerts. The alerts are fine-tuned
for low-noise and good defaults.

This feature is disable by default. If you would like to enable it then set:

.. code-block:: yaml

    enablePrometheusStack: true

We recommend you enable this if haven't yet installed Prometheus on your cluster.

The alerts are currently based on kube-prometheus-stack but we expect to diverge more over time.