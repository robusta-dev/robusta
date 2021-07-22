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
Robusta can schedule and run playbooks periodically.

This trigger will fire every ``seconds_delay`` seconds for ``repeat`` times

**Note:** In order to run a playbook indefinitely, specify ``repeat=-1``

For example:

.. code-block:: python

    @on_recurring_trigger(seconds_delay=10, repeat=3)
    def my_scheduled_playbook(event: RecurringTriggerEvent):
        logging.info(f"My scheduled playbook is running for the {event.recurrence} time")

Sinks
-------------
| Playbooks results can be forwarded to one or more sinks. See :ref:`Playbooks sinks` for details.
| For that to happen, we have to create ``Finding`` and ``Enrichments`` during the playbooks processing.
| The Robusta platform will automatically forward it to the configured sinks

Finding
^^^^^^^^^^^^^^^^^
| The ``Finding`` contains the base information of the playbooks result.
| Creating a ``Finding`` is easy:

.. code-block:: python

    @on_recurring_trigger(seconds_delay=10, repeat=3)
    def my_scheduled_playbook(event: RecurringTriggerEvent):
        event.processing_context.create_finding(
            title=f"My scheduled playbook is running for the {event.recurrence} time",
            severity=FindingSeverity.INFO
    )

Enrichments
^^^^^^^^^^^^^^^^^
| Each ``Finding`` can contain any number of ``Enrichments``.
| Each ``Enrichment`` has a list of ``blocks`` describing it:
* **MarkdownBlock:** - A text block
* **DividerBlock:** - Dividing section between ``Enrichment`` parts. (If the sink supports that)
* **HeaderBlock:** - A header block
* **ListBlock:** - A block containing list of items
* **TableBlock:** - A block containing table of items
* **KubernetesFieldsBlock:** - A block containing information describing kubernetes fields
* **DiffsBlock:** - A block containing information describing yaml diff attributes
* **JsonBlock:** - A block containing any json data
* **FileBlock:** - A block containing any file with the file data
* **CallbackBlock:** - A block containing callback information, that can be invoked back from the sink. (a Slack button for example, running some command)

| **Note:** - Not all block types supported by all sinks. If an unsupported block arrives to a sink, it will be ignored

| Adding an ``Enrichment``:

.. code-block:: python

    my_log_file_data = "..."
    event.processing_context.finding.add_enrichment([FileBlock("log.txt", my_log_file_data)])
