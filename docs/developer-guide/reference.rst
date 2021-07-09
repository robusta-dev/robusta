Developer API
#############

Trigger Types
-------------

Kubernetes Events
^^^^^^^^^^^^^^^^^
These playbooks are triggered when Kubernetes objects are created, modified, or updated.

A quick example:

.. code-block:: python

    @on_deployment_create
    def deployment_creation_playbook(event: DeploymentEvent):
        print("pod created with name {event.obj.metadata.name} and namespace {event.obj.metadata.name}")


The triggers for monitoring resources are as follows, where ``<resource>`` is the name of
a Kubernetes resource:

* ``@on_<resource>_create``
* ``@on_<resource>_update``
* ``@on_<resource>_delete``
* ``@on_<resource>_all_changes``

For example, the creation of  Kubernetes services can be monitored with the trigger ``@on_service_create``.

All Kubernetes triggers allow filtering events by the name and namespace of the Kubernetes object. For example:

.. code-block:: python

    @on_deployment_create(name_prefix="some_name", namespace_prefix="some_namespace")
    def deployment_creation_playbook(event: DeploymentEvent):
        print("pod created with name {event.obj.metadata.name} and namespace {event.obj.metadata.name}")

Triggers like ``@on_deployment_update`` and ``@on_deployment_all_changes`` run when a Kubernetes
object was modified and therefore playbooks receive both the old and new version of the Kubernetes
object so that they can be easily compared:

.. code-block:: python

    @on_deployment_all_changes
    def track_deployment_(event: DeploymentEvent, config: DeploymentBabysitterConfig):
        if event.operation != K8sOperationType.UPDATE:
            return
        print(f"new deployment spec is {event.obj.spec} and old spec is {event.old_obj.spec}")

Prometheus Alerts
^^^^^^^^^^^^^^^^^

Robusta can run playbooks when Prometheus alerts are triggered. For example

.. code-block:: python

    @on_pod_prometheus_alert(alert_name="HighCPUAlert", status="firing")
    def high_cpu(alert: PrometheusPodAlert):
        print(f'pod {alert.obj} has high cpu alert: {alert.alert}')

Manual Triggers
---------------
Robusta can run playbooks on manual triggers. For example:

.. code-block:: python

    @on_manual_trigger
    def some_playbook(event: ManualTriggerEvent):
        print(f"should do something. value of foo is {event.data['foo']}")

To trigger this playbook run the following command from within your Kubernetes cluster:

.. code-block:: bash

    robusta trigger some_playbook

If the playbook has parameters, the parameters values can be passed in as follows:

.. code-block:: bash

    robusta trigger some_playbook some_param=some_value other_param=other_value

Recurring Triggers
------------------
Robusta can schedule and run playbooks periodically. For example:

.. code-block:: python

    @on_recurring_trigger(seconds_delay=10, repeat=3)
    def my_scheduled_playbook(event: RecurringTriggerEvent):
        logging.info(f"My scheduled playbook is running for the {event.recurrence} time")
