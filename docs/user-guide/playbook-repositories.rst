Playbook Repositories
################################

Robusta's playbooks are defined in git repositories, with project format of a python package.

In order to use playbooks, you need to include the relevant repositories.

A playbook repository can be a git repository url, or a path to a directory on the file system.

Note:
    Robusta does not watch for changes on git repositories. Playbooks are loaded from the repository when the server
    starts or the configuration changes.

Both should contains project format of a python package.

Configuring playbook repositories
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Playbook repositories are defined using the ``playbookRepos`` Helm value:

.. code-block:: yaml

    playbookRepos:
      robusta_playbooks:
        url: "file:///etc/robusta/playbooks/defaults"


This configuration above, is the configuration of Robusta's default playbooks.

We can load a playbook repository using a git url:

.. code-block:: yaml

    playbookRepos:
      robusta_playbooks:
        url: "git@github.com:robusta-dev/robusta-playbooks.git"
        key: |-
          -----BEGIN OPENSSH PRIVATE KEY-----
          ewfrcfsfvC1rZXktdjEAAAAABG5vb.....
          -----END OPENSSH PRIVATE KEY-----


The ``key`` should contain a deployment key, with ``read`` access.

You can load any number of playbook repositories.

If you remove an item from the ``playbookRepos`` value, it cannot be used, even if it's found locally.


Building your own playbook repository
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
You can build your own playbook repository.
You should build a python project, with the following structure:

.. code-block:: yaml

    root
      pyproject.toml
      my_playbook_repo
        my_actions.py

The package name in your ``pyproject.toml`` should match the name of the inner playbooks directory.
In addition, if your playbook requires additional python dependencies, list those in your ``pyproject.toml`` file
and Robusta will install them with your playbooks repository.

An example ``pyproject.toml`` for the repository above would be:

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


Ok, so our playbook is ready! Excellent. Now we need to deploy it.

Deploying your own playbook repository
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
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
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
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

