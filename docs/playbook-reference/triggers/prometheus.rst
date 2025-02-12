Prometheus and AlertManager
#############################

Robusta can :ref:`improve your existing Prometheus alerts <Enhanced Prometheus Alerts>`. It can also execute
:ref:`Remediation Actions <Automatic Remediation>` in response to alerts.

Prerequisites
---------------
AlertManager must be connected to Robusta. Refer to :ref:`Integrating AlertManager and Prometheus`.

Triggers
-----------

The following triggers are available for Prometheus alerts:

.. _on_prometheus_alert:

.. details:: on_prometheus_alert


    ``on_prometheus_alert`` fires when a Prometheus alert starts or stops firing.

    .. admonition:: Example

        Run the ``ps aux`` command when HostHighCpuLoad fires. Output will be sent as a :ref:`Robusta notification <sinks-overview>`. The node on which the command executes will be selected according to the alert labels.

        .. code-block:: yaml

            customPlaybooks:
            - triggers:
              - on_prometheus_alert:
                  alert_name: HostHighCpuLoad
                  scope:
                    include:
                    - labels:
                        - "deployment=nginx"
              actions:
              - node_bash_enricher:
                  bash_command: ps aux

    ``on_prometheus_alert`` supports the following parameters:

    .. pydantic-model:: robusta.integrations.prometheus.trigger.PrometheusAlertTrigger

    The ``scope`` filtering mechanism works exactly as it does for sinks
    (see :ref:`sink-scope-matching` for more information), but you can only
    atch on ``labels`` and ``annotations`` in this case.

Recommended Actions
---------------------

There are dedicated playbook actions for ``on_prometheus_alert``:

* :ref:`Prometheus Enrichers`
* :ref:`Prometheus Silencers`

Additionally, almost all :ref:`Event Enrichment` actions support ``on_prometheus_alert``.

Running Python Code in Response to a Alert
---------------------------------------------

If the :ref:`builtin actions <Actions Reference>` are insufficient, you can extend Robusta with your own actions that respond to Prometheus alerts.

.. admonition:: example action

    .. code-block:: python

        @action
        def my_action(alert: PrometheusKubernetesAlert):
            print(f"The alert {alert.alert_name} fired on pod {alert.pod.metadata.name}")
            print(f"The pod has these processes:", alert.pod.exec("ps aux"))
            print(f"The pod has {len(alert.pod.spec.containers)} containers")


``alert.pod`` is a Kubernetes pod object. It will exist if the Prometheus alert had a ``pod`` label and the pod is alive
when the playbook runs. There are also ``node``, ``deployment``, and ``daemonset`` fields.

Refer to :ref:`Developing New Actions` for more details.
