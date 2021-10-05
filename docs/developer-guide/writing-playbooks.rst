Writing playbooks
#################

Extending Robusta with your own Python playbook takes no longer than 5 minutes.

We recommend sharing your playbook back with the community and adding it to the official Robusta repository by opening a PR on GitHub.

If you are interested in creating playbooks without writing code, contact us!

Setting up a playbooks directory
-------------------------------------------------------------
Before a custom playbook can be configured in ``active_playbooks.yaml`` it must first be loaded into Robusta as part of a *playbook_directory*.
(For Robusta's built-in playbooks you skip this step.)

A *playbook_directory* is a directory of Python files:

.. code-block:: bash

    mkdir example_playbooks
    touch example_playbooks/hello.py

Edit ``hello.py``:

.. code-block:: python

    from robusta.api import *

    @on_pod_create()
    def hello_world_playbook(event: PodEvent):
        logging.info(f"Pod {event.obj.metadata.name} created on namespace {event.obj.metadata.namespace}")


Load the **playbook_directory** into Robusta:

.. code-block:: bash

    robusta playbooks load my-custom-playbooks-dir

Configuring your playbook
-------------------------------------------------------------
Once the **playbook_directory** has been loaded, you can configure your playbook the same way as built-in playbooks.
Add ``hello_world_playbook`` to your ``active_playbooks.yaml`` and deploy the new ``active_playbooks.yaml`` to the cluster:

.. code-block:: bash

    robusta playbooks configure active_playbooks.yaml

That's it! Every time a Kubernetes pod is created in the cluster, the above log line will be printed to the robusta-runner logs.

Go ahead and try it. Create a deployment (and therefore a pod):

.. code-block:: bash

    kubectl create deployment first-playbook-test-deployment --image=busybox -- echo "Hello World - Robusta"


Robusta Playground
---------------------------

To experiment with the Robusta API, you can open an interactive Python shell with the Robusta
API preconfigured:

.. code-block:: bash

    $ robusta playground
    # <stack traces are dumped... you can ignore this>
    # ...

    $ dep = Deployment.from_image("stress-test", "busybox", "ls /")
    $ dep.create()


This interactive shell runs inside the Robusta runner, so don't do this in production.
This feature is powered by `python-manhole <https://github.com/ionelmc/python-manhole>`_ and
is only enabled when the environment variable ``ENABLE_MANHOLE`` is set to ``true``.

