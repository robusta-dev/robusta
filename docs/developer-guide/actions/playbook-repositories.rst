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

First, enable persistent playbooks storage by setting the helm value in the Robusta's configuration file (generated_values.yaml):

.. code-block:: yaml

    playbooksPersistentVolume: true
.. code-block:: bash

     helm upgrade robusta robusta/robusta --values=generated_values.yaml

Now use the Robusta CLI to load your repository:

.. code-block:: bash

     robusta playbooks push ./my-playbooks-project-root

This copies the repository to a mounted persistent volume on the Robusta runner at ``/etc/robusta/playbooks/storage``.  The actions inside the repository are now loaded and ready for use.


Changing Robusta's default playbooks
----------------------------------------
Some users may want to change Robusta's default playbooks.

You can override the *entire* default playbooks package by loading another package with the name ``robusta_playbooks``,
or you can override a single ``action`` just by implementing and loading another ``action`` with the same name.

For example, if you want to override the ``resource_babysitter`` action:

1. Create a playbooks package for your ``action``.
2. Create a new ``resource_babysitter`` action in one of the package files.
3. Push the playbooks package:

.. code-block:: bash

    robusta playbooks push ./my-custom-playbooks-package
