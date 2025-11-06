.. _Loading Custom Actions into Robusta:

Loading Custom Actions into Robusta
####################################

Prerequisites
--------------

You have a :ref:`Playbook Repository <Creating Playbook Repositories>` with at least one action.

This repository can be in git, or just a local folder.

Loading Custom Actions into Robusta
-------------------------------------

You can load your playbook in one of two ways:

1. From a git repository, :ref:`as described in the configuration guide <Loading External Actions>`
2. From a local directory, using ``robusta playbooks push``

We'll describe the second option which is convenient for development.

Using a local directory
^^^^^^^^^^^^^^^^^^^^^^^^^

Enable persistent playbooks storage in the Robusta's Helm values (generated_values.yaml):

.. code-block:: yaml

    playbooksPersistentVolume: true

Apply the change:

.. code-block:: bash

     helm upgrade robusta robusta/robusta --values=generated_values.yaml

Use the Robusta CLI to load your repository:

.. code-block:: bash

     robusta playbooks push ./my-playbooks-project-root

This copies your repository to a mounted persistent volume in the robusta-runner deployment at ``/etc/robusta/playbooks/storage``.

The actions inside the repository are now loaded and ready for use.
