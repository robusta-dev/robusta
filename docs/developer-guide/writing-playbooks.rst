Writing playbooks
#################

Extending Robusta with your own Python playbook takes no longer than 5 minutes.

We recommend sharing your playbook back with the community and adding it to the official Robusta repository by opening a PR on GitHub.

If you are interested in creating playbooks without writing code, contact us!

Downloading the built-in playbooks
-----------------------------------

Lets get started by downloading the example playbooks. You can also view them on `GitHub <https://github.com/robusta-dev/robusta/tree/master/playbooks>`_.

.. code-block:: bash

    robusta examples

Now lets install some extra Python packages so that we have autocompletion in our IDE:

.. code-block:: bash

    pip3 install robusta-cli

You can now open the python files in the ``playbooks/`` directory in your favorite IDE and start modifying them!

Adding your own Hello World playbook
-------------------------------------
Create a new file in the playbooks directory named ``hello-world-playbook.py`` with the following contents:

.. code-block:: python

    from robusta.api import *

    @on_pod_create()
    def hello_world_playbook(event: PodEvent):
        logging.info(f"Pod {event.obj.metadata.name} created on namespace {event.obj.metadata.namespace}")


Activate the playbook in ``active_playbooks.yaml``:

.. code-block:: yaml

    active_playbooks:
    - name: "hello_world_playbook"

Finally, deploy the newly created playbook:

.. code-block:: bash

    robusta playbooks deploy ./playbooks

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

