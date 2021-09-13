More Robusta CLI Commands
##############################

The ``robusta`` cli has additional commands for managing playbooks in your cluster.

Initial configuration
------------------------------------------
To initially configure your ``active_playbooks.yaml`` file run

.. code-block:: python

   robusta gen-config


Viewing active playbooks
------------------------------------------
To view the currently active playbooks in your cluster run:

.. code-block:: python

   robusta playbooks list

Pulling cluster playbooks locally
------------------------------------------
You can download your cluster's playbook directory at any time. This will fetch both the code and yaml files:

.. code-block:: python

   robusta playbooks pull

| **params:** ``--playbooks-directory TARGET_LOCAL_DIRECTORY``, default to current directory
