Custom playbook repositories
################################

First read the :ref:`the guide on writing playbook actions <The Basics>` if you haven't already.

Creating your own playbook repository
-----------------------------------------

A playbook repository is a directory with the following structure:

.. code-block:: yaml

    root
      pyproject.toml
      my_playbook_repo
        my_actions.py

An example ``pyproject.toml`` would be:

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

The package name in your ``pyproject.toml`` (*my_playbook_repo* in the above example) must match the name of the
inner playbooks directory.

If your playbook requires additional python dependencies, list those in your ``pyproject.toml`` file
and Robusta will install them with your playbooks repository.

Loading your own playbook repository
-------------------------------------------

You can load your playbook in one of two ways:

1. From a git repository, :ref:`as described in the configuration guide <Loading additional playbooks>`
2. Using ``robusta playbooks push``

We'll describe the second option which is convenient for development. It allows deploying playbooks rapidly while you
develop them.

First, persistent playbooks storage by setting the helm value:

.. code-block:: yaml

    playbooksPersistentVolume: true

Now use the Robusta CLI to load your repository:

.. code-block:: bash

     robusta playbooks push ./my-playbooks-project-root

This copies the repository to a mounted persistent volume on the Robusta runner at ``/etc/robusta/playbooks/storage``

Lastly, add this directory to the Helm values:

.. code-block:: yaml

    playbookRepos:
      my_playbook_repo:
        url: "file:///etc/robusta/playbooks/storage/my-playbooks-project-root"

After setting this up once, you only need to run ``robusta playbooks push`` to update your playbooks.

Changing Robusta's default playbooks
----------------------------------------
Some users may want to change Robusta's default playbooks.

1. Copy the default playbooks package, locally or to another git repository.
2. Make your changes.
3. Configure Robusta to use your package, instead of the default one. Update ``playbookRepos`` in the Helm chart to use your playbooks. For example:

.. code-block:: yaml

    playbookRepos:
      robusta_playbooks:
        url: "file:///etc/robusta/playbooks/storage/my-local-default-repository-copy"

As described above, we will need to push this local repository to the Robusta runner:

.. code-block:: bash

    robusta playbooks push ./my-local-default-repository-copy
