The Basics
################################

Introduction
------------------
You can add your own playbook actions to Robusta with Python.

Please consider sharing your playbook by opening a PR on Github.

If you are interested in creating playbooks without writing code, contact us!

Building your own playbook repository
-----------------------------------------
You can build your own playbook repository.
You should build a python project with a ``pyproject.toml`` in it's root.

An example ``pyproject.toml`` for the repository would be:

.. code-block:: bash

    [tool.poetry]
    name = "my_playbook_repo"
    version = "0.0.1"
    description = ""
    authors = ["USER NAME <myuser@users.noreply.github.com>"]

    [tool.poetry.dependencies]
    some-dependency = "^1.2.3"

    [tool.poetry.dev-dependencies]
    robusta-cli = "^0.8.9"

    [build-system]
    requires = ["poetry-core>=1.0.0"]
    build-backend = "poetry.core.masonry.api"

If your playbook requires additional python dependencies, list those in your ``pyproject.toml`` file
and Robusta will install them with your playbooks repository.

Your project should match the following structure:

.. code-block:: yaml

    root
      pyproject.toml
      my_playbook_repo
        my_actions.py

The package name in your ``pyproject.toml`` should match the name of the inner playbooks directory.
(``my_playbook_repo`` on the example above)

Ok, so our playbook is ready! Excellent. Now we need to deploy it.

Deploying your own playbook repository
-------------------------------------------
As any other playbook, we have to options for loading it.
The first, using a git repository (public or private).
In order to do that, we have to upload our project to a git repository, and then configure it:

.. code-block:: yaml

    playbookRepos:
      my_playbook_repo:
        url: "git@github.com:my-user/my-playbook-repo.git"
        key: |-
          -----BEGIN OPENSSH PRIVATE KEY-----
          ewfrcfsfvC1rZXktdjEAAAAABG5vb.....
          -----END OPENSSH PRIVATE KEY-----

Now, Robusta will load our playbooks from this git repository.

We have another option, which is more convenient while building a playbook and deploying it frequently.

We can push our local playbooks repository, directly into Robusta.
In order to do that, we have to enable playbooks persistent storage on our cluster, by setting the helm value
``playbooksPersistentVolume`` to ``true``

When Robusta is configured that way, we can use the Robusta CLI to load playbooks:

.. code-block:: bash

     robusta playbooks push ./my-playbooks-project-root

This command will load the playbook repository into a mounted persistent volume on the Robusta runner.
This volume is mounted to: ``/etc/robusta/playbooks/storage``

Now, we just need to load this playbooks repository to the Robusta runner:

.. code-block:: yaml

    playbookRepos:
      my_playbook_repo:
        url: "file:///etc/robusta/playbooks/storage/my-playbooks-project-root"

That's it!

Now we can change playbooks locally, and just load them using ``robusta playbooks push ...``
The Robusta runner watch for changes, and reload the playbooks when a change occurs.

Changing Robusta's default playbooks
----------------------------------------
Some users may want to change Robusta's default playbooks.
You can easily do that.

Copy the default playbooks package, locally or to another git repository.
Make your required changes.

Now just configure Robusta to use your package, instead of the default one.
Just replace the ``url`` in the ``playbookRepos`` helm value, for the ``robusta_playbooks`` repository.

For example, if we have it locally:

.. code-block:: yaml

    playbookRepos:
      robusta_playbooks:
        url: "file:///etc/robusta/playbooks/storage/my-local-default-repository-copy"

As described above, we will need to push this local repository to the Robusta runner:

.. code-block:: bash

    robusta playbooks push ./my-local-default-repository-copy

Implementing your first playbook
-------------------------------------------------------------
Let's create our first playbooks reposirory.

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

Now, we just need to configure Robusta to use our new playbook package.
Update the ``playbookRepos`` helm value:

.. code-block:: yaml

    playbookRepos:
      example_playbooks:
        url: "file:///etc/robusta/playbooks/storage/example_playbooks"


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
In our above action, we want to exec commands on a pod, so obviously we'll need a pod as input.
Therefore the action takes a ``PodEvent``.

Some actions are interested in **changes** and not just static resources - for example, a playbook that shows you a diff
of what changed. These actions should take one of the ChangeEvent classes. For example, ``PodChangeEvent``

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

Credits
--------------------
Robusta uses many open source libraries, but two of them outshine all others:

1. `Hikaru <https://hikaru.readthedocs.io/>`_
2. `Pydantic <https://pydantic-docs.helpmanual.io/>`_

We owe a special thank you to Tom Carroll and Samuel Colvin.

A further thank you is due to the countless developers who created other libraries we use. You rock.

Common gotchas
-------------------
Datetime fields in Kubernetes resources are strings, not datetime objects. Use the utility function ``parse_kubernetes_datetime`` to convert them.