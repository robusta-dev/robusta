Configuration Guide
################################

Robusta is configured using Helm values. All possible values can be found in
`values.yaml <https://github.com/robusta-dev/robusta/blob/master/helm/robusta/values.yaml>`_

This page documents the important values.

Defining playbooks
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Playbooks are defined using ``customPlaybooks``:

.. code-block:: yaml

    customPlaybooks:
    - triggers:
      - on_deployment_update:
      actions:
      - resource_babysitter:
          fields_to_monitor: ["status.conditions"]
      sinks:
      - "slack sink"

See the documentation for :ref:`Triggers`, :ref:`Actions`, and :ref:`Sinks`.

Enabling a playbook multiple times
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
      - "slack sink"

    - triggers:
      - on_deployment_update:
          name_prefix: OtherApp
      actions:
      - add_deployment_lines_to_grafana:
          grafana_api_key: grafana_key_goes_here
          grafana_dashboard_uid: id_for_dashboard2
          grafana_url: http://grafana.namespace.svc
      sinks:
      - "slack sink"

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
      - "slack sink"

    - triggers:
      - on_deployment_update:
          name_prefix: OtherApp
      actions:
      - add_deployment_lines_to_grafana:
          grafana_dashboard_uid: id_for_dashboard2
      sinks:
      - "slack sink"

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

.. note:: In order to get a Slack key run: ``robusta integrations slack``.

.. code-block:: yaml

    sinks_config:
    - slack_sink:
        name: slack sink
        api_key: {{ .Values.slackApiKey }}
        slack_channel: {{ required "A valid .Values.slackChannel entry is required!" .Values.slackChannel }}
        default: false
    - robusta_sink:
        name: robusta_ui_sink
        token: {{ .Values.robustaApiKey }}
        default: true


    - sink_name: "my kafka sink"
      sink_type: "kafka"
      params:
        kafka_url: "localhost:9092"
        topic: "robusta-playbooks"
    - sink_name: "datadog events"
      sink_type: "datadog"
      params:
        api_key: "MY DATADOG ACCOUNT API KEY"


By default, all playbooks will forward the results to the default sinks.
The default sinks list can be overridden, per playbook:

.. code-block:: yaml

     - name: "add_deployment_lines_to_grafana"
       sinks:
       - "my kafka sink"
       action_params:
         grafana_dashboard_uid: "uid_from_url"
         grafana_api_key: "grafana_api_key_with_editor_role"
         grafana_service_name: "grafana.namespace.svc.cluster.local:3000"

