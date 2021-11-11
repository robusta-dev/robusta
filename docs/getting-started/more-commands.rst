More CLI Commands
##############################

The ``robusta`` cli has commands for managing playbooks in your cluster:

Generate Helm configuration
------------------------------------------
To generate a Helm ``values.yaml`` file for Robusta:

.. code-block:: bash

   robusta gen-config

Edit Robusta's internal configuration
--------------------------------------

To bypass Helm and update Robusta's configuration directly:

.. code-block:: bash

   robusta edit-config

.. warning:: These changes will be overridden by Helm next time it updates your cluster. Furthermore, the internal Robusta configuration file has a slightly different format than the Helm values.

View active playbooks
------------------------------------------
To view the currently active playbooks in your cluster run:

.. code-block:: bash

   robusta playbooks list

Pulling cluster playbooks locally
------------------------------------------
To download your cluster's playbook directory at any time:

.. code-block:: bash

   robusta playbooks pull

| **params:** ``--playbooks-directory TARGET_LOCAL_DIRECTORY``, default to current directory

Uninstalling Robusta
---------------------

Robusta is installed using ``helm``. Running ``helm uninstall robusta`` removes all the installed components.
