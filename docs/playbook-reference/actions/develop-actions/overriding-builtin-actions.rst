Changing Robusta's builtin actions
###################################

Some users may want to change playbook actions built into Robusta. This is useful when fixing bugs or adding new features.

Override a single builtin action
-----------------------------------------
To do so, implement and load another action with the same name. For example, to override the builtin ``logs_enricher`` action,
just load your own action named ``logs_enricher``.

Override all default actions at once
-----------------------------------------
If you're going to modify many builtin playbooks, it may be easier to fork the defaults and load everything at once from your fork.
(By fork, we mean copy-pasting the ``playbooks/robusta_playbooks`` folder, not a literal git fork.)

To do so, copy the ``playbooks/robusta_playbooks`` folder to a custom playbook repository, and load it under the
name ``robusta_playbooks``. This will override all the defaults with your version.

For example, if you want to override the ``resource_babysitter`` action:

1. Create a playbooks package for your action.
2. Create a new ``resource_babysitter`` action inside it.
3. Push the playbooks package:

.. code-block:: bash

    robusta playbooks push ./my-custom-playbooks-package
