.. _Creating Playbook Repositories:

Creating Playbook Repositories
################################

To deliver install custom actions into Robusta, you'll need to package them up. This is done with a git repository in a specific format.

What is a Playbook Repository?
-------------------------------
A playbook repository is a directory with the following structure:

.. code-block:: yaml

    root
      pyproject.toml
      my_playbook_repo
        my_actions.py

.. warning:: Do **not** use the directory name "robusta_playbooks". This name is reserved and using it will override the built-in Robusta playbooks

An example ``pyproject.toml`` would be:

.. code-block:: bash

    [tool.poetry]
    name = "my_playbook_repo"
    version = "0.0.1"
    description = ""
    authors = ["USER NAME <myuser@users.noreply.github.com>"]

    [tool.poetry.dependencies]
    # if your playbook requires additional dependencies, add them here
    #some-dependency = "^1.2.3"

    [tool.poetry.dev-dependencies]
    robusta-api = "^0.14"

    [build-system]
    requires = ["poetry-core>=1.0.0"]
    build-backend = "poetry.core.masonry.api"

The package name in your ``pyproject.toml`` (*my_playbook_repo* in the above example) must match the name of the
inner playbooks directory.

If your playbook requires additional python dependencies, list those in your ``pyproject.toml`` file
and Robusta will install them with your playbooks repository.

Next Steps
------------

Now that you've created a playbook repository, :ref:`load it into Robusta <Loading Custom Actions into Robusta>`.
