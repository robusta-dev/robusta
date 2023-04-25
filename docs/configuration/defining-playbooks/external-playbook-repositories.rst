Loading External Actions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Robusta can load playbook actions from external git repositories. This extends Robusta with additional actions for
use in :ref:`customPlaybooks<customPlaybooks>`.

.. warning::

    Robusta does not watch for changes in git repositories. Playbooks are reloaded when:

    * Robusta starts
    * Robusta's configuration changes
    * ``robusta playbooks reload`` is run

External actions are loaded using the ``playbookRepos`` Helm value, with either HTTPs or SSH.

Loading Actions from Public Git Repo
------------------------------------------

Use HTTPs to load actions:

.. code-block:: yaml

    playbookRepos:
      # add playbooks from https://github.com/robusta-dev/robusta-chaos
      my_extra_playbooks:
        url: "https://github.com/robusta-dev/robusta-chaos.git"


Loading Actions from Private Git Repos
-----------------------------------------

For private repos, load actions using SSH not HTTPs.

This method works for public repos too:

.. code-block:: yaml

    playbookRepos:
      # add the same playbooks as above, this time over ssh
      my_extra_playbooks:
        url: "git@github.com:robusta-dev/robusta-chaos.git"
        key: |-
          -----BEGIN OPENSSH PRIVATE KEY-----
          ewfrcfsfvC1rZXktdjEAAAAABG5vb.....
          -----END OPENSSH PRIVATE KEY-----

The ``key`` parameter must contain a deployment key with ``read`` access. This parameter is required when accessing a
git repo over ssh, even for public repositories.

Handling Secrets
*******************

To avoid including Secrets in ``playbookRepos``, save your SSH key in a
`Kubernetes Secret <https://kubernetes.io/docs/concepts/configuration/secret/>`_.
Then reference it using an environment variable:

.. code-block:: yaml

    additional_env_vars:
     - name: GITHUB_SSH_KEY
       valueFrom:
         secretKeyRef:
           name: ssh-key
           key: id_rsa

    playbookRepos:
      my_extra_playbooks:
        url: "git@github.com:robusta-dev/robusta-chaos.git"
        key: "{{env.GITHUB_SSH_KEY}}"
