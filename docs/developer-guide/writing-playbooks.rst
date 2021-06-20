Writing playbooks
#################

You can write your own playbooks to extend Robusta and automate tasks not covered by built-in playbooks.
We recommend sharing your playbook back with the community and adding it to the official Robusta repository by opening a PR on GitHub.

If you don't know how to program in Python, the Robusta team would be happy to write playbooks for you.

Writing your first playbook
---------------------------

Lets get started by downloading the example playbooks

.. code-block:: bash

    robusta examples

Now lets install some extra Python packages so that we have autocompletion in our IDE:

.. code-block:: bash

    pip3 install robusta-cli git+https://github.com/aantn/k8s git+https://github.com/aantn/hikaru.git@main

Now open the example playbooks in your favorite IDE and start modifying them!

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

