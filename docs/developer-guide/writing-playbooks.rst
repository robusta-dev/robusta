Writing playbook actions
################################

Introduction
------------------
You can add your own playbook actions to Robusta with Python.

Please consider sharing your playbook by opening a PR on Github.

If you are interested in creating playbooks without writing code, contact us!

Playbook packages
-------------------------------------------------------------
Before custom actions can be used, they must first be loaded into Robusta.

A *playbooks package* is a directory of Python files with a special ``pyproject.toml`` file:

.. code-block:: bash

    mkdir example_playbooks
    touch example_playbooks/hello.py

Lets write the action itself in ``example_playbooks.hello.py``:

.. code-block:: python

    from robusta.api import *

    @action
    def my_action(event: PodEvent):
        # we have full access to the pod on which the alert fired
        pod = event.get_pod()
        pod_name = pod.metadata.name
        pod_logs = pod.get_logs()
        pod_processes = pod.exec("ps aux")

        # this is how you send data to slack or other destinations
        event.add_enrichment([
            MarkdownBlock("*Oh no!* An alert occurred on " + pod_name)
            FileBlock("crashing-pod.log", pod_logs)
        ])

Load the playbooks package into Robusta:

.. code-block:: bash

    robusta playbooks push example_playbooks

Using your action
-------------------------------------------------------------
Once the playbooks package is loaded, you can use your action.

The action above receives a ``PodEvent`` so it can be used for pod-related triggers.

.. code-block:: yaml
   :emphasize-lines: 5

   customPlaybooks:
   - triggers:
     - on_pod_update: {}
     actions:
     - my_action: {}

Choosing an event class
------------------------
Our above action needs a pod to run so the playbook takes a ``PodEvent``.

Some actions need **change** to run - for example, a playbook that shows you a diff of what changed. These actions should
take one of the ChangeEvent classes. For example, ``PodChangeEvent``

.. code-block:: python

   @action
   def pod_change_monitor(event: PodChangeEvent):
      logging.info(f"new object: {event.obj})
      logging.info(f"old object: {event.old_obj})

``PodChangeEvent`` will fire on creations, updates, and deletions. You can check the event type with ``event.operation``.

To write a more general action that monitors all Kubernetes changes, we can use ``KubernetesAnyChangeEvent``.

You should always use the highest-possible event class when writing actions. This will let your action be used in as many
scenarios as possible. See :ref:`Event Hierarchy` for details.

Actions with parameters
-------------------------------
Any action can define variables it needs. There are two steps:

1. Define a class inheriting from ``ActionParams`` and use type-annotations to define variables
2. Add the parameter class as an additional argument to the action

For example:

.. code-block:: python

   from robusta.api import *

   class BashParams(ActionParams):
      bash_command: str

   @action
   def pod_bash_enricher(event: PodEvent, params: BashParams):
       pod = event.get_pod()
       if not pod:
           logging.error(f"cannot run PodBashEnricher on event with no pod: {event}")
           return

       block_list: List[BaseBlock] = []
       exec_result = pod.exec(params.bash_command)
       block_list.append(MarkdownBlock(f"Command results for *{params.bash_command}:*"))
       block_list.append(MarkdownBlock(exec_result))
       event.add_enrichment(block_list)

We can now define the ``bash_command`` parameter in ``values.yaml``:

.. code-block:: yaml

   customPlaybooks:
   - triggers:
     - on_pod_update: {}
     actions:
     - pod_bash_enricher:
         bash_command: "ls -al /"

Under the hood, we use the excellent `Pydantic <https://pydantic-docs.helpmanual.io/>`_ library to implement this.

Please consult Pydantic's documentation for details. ``ActionParams`` is a drop-in substitute for Pydantic's ``BaseModel``.

Rate-limiting
-------------

Sometimes you need to prevent an action from running too often. You can use the ``RateLimiter`` class for that:

.. code-block:: python
   :emphasize-lines: 5-10

   from robusta.api import *

   @action
   def argo_app_sync(event: ExecutionBaseEvent, params: ArgoAppParams):
       if not RateLimiter.mark_and_test(
           "argo_app_sync",
           params.argo_url + params.argo_app_name,
           params.rate_limit_seconds,
       ):
           return
      ...

The second parameter to ``RateLimiter.mark_and_test`` defines a key used for checking the rate limit. Each key is rate-limited individually.

Common gotchas
-------------------
Datetime fields in Kubernetes resources are strings, not datetime objects. Use the utility function ``parse_kubernetes_datetime`` to convert them.