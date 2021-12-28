Playbook Repositories
################################

Robusta's playbooks are defined in git repositories.

To use playbooks, include the relevant repository.

A playbook repository can be a git repository url, or a path to a directory on the file system.

Note:
    Robusta does not watch for changes on git repositories. Playbooks are loaded from the repository when the server
    starts or the configuration changes.

Configuring playbook repositories
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Playbook repositories are defined using the ``playbookRepos`` Helm value:

.. code-block:: yaml

    playbookRepos:
      robusta_playbooks:
        url: "file:///etc/robusta/playbooks/defaults"


This configuration defines Robusta's default playbooks.

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

If you remove an item from the ``playbookRepos`` value, it will not be used, even if it's found locally.

