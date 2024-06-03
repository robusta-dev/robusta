Playbook API Changes
################################

.. admonition:: Do I need to read this page?

    Most Robusta users can ignore this page.

    This page only applies to users who wrote custom playbook actions in Python.


This page documents breaking changes to the Robusta API, and how to update custom playbook actions between versions.

Using new 'robusta-api' package from Robusta version 0.14
===============================================

Old versions used the ``robusta-cli`` package for the api headers. Please use the new ``robusta-api`` package.

Updating Custom Playbooks to Robusta 0.10.17
===============================================

In Robusta 0.10.17 we updated the Hikaru dependency to a newer version.

To support this change in your playbook actions, apply the following changes.

Update pyproject.toml
-----------------------

Remove ``hikaru`` and ``kubernetes`` from your playbook repo's ``pyproject.toml``. These are managed by Robusta itself
and listing them in ``pyproject.toml`` can cause the library version to be downgraded.

.. code-block:: python

   [tool.poetry.dependencies]
   # remove these lines!
   #hikaru = ...
   #kubernetes = ...

Update hikaru imports
----------------------

Change your imports from ``hikaru.model`` to ``hikaru.model.rel_1_26``.

.. code-block:: python

   # Old import
   from hikaru.model import Node

   # New import
   from hikaru.model.rel_1_26 import Node


Update all Kubernetes listing functions
---------------------------------------------

Resource-listing functions have moved. For example, ``Deployment.listNamespacedDeployment`` is now ``DeploymentList.listNamespacedDeployment``.

.. code-block:: python

   # Old method
   Deployment.listNamespacedDeployment()

   # New method
   DeploymentList.listNamespacedDeployment()

Other changes
-----------------------

The Event object was updated to a newer Kubernetes API version. This change is unlikely to effect your code, but if
necessary refer to the `Kubernetes deprecation guide on Events <https://kubernetes.io/docs/reference/using-api/deprecation-guide/#event-v125>`_.

For the complete list of Hikaru changes, refer to the `Hikaru release notes <https://github.com/haxsaw/hikaru/blob/main/release_notes.rst>`_.
