Hello World playbook
#####################

With Robusta, implementing a playbook takes no longer than 5 minutes.

Lets do it!

Playbook code
---------------------------

Start by creating a new file in the playbooks directory named: ``hello-world-playbook.py``

Edit it, and add the following:

.. code-block:: python

    from robusta.api import *

    @on_pod_create()
    def hello_world_playbook(event: PodEvent):
        logging.info(f"Pod {event.obj.metadata.name} created on namespace {event.obj.metadata.namespace}")


Now lets activate the playbook in the ``active_playbooks.yaml`` file:

.. code-block:: yaml

    active_playbooks:
    - name: "hello_world_playbook"

Now deploy the newly created playbook:

.. code-block:: bash

    robusta deploy playbooks

That's it!

Now, every time a Kubernetes pod is created in the cluster, the above log line will be printed to the robusta-runner logs.