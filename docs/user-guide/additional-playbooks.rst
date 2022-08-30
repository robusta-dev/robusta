Loading additional playbooks
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Playbook actions are loaded into Robusta using the ``playbookRepos`` Helm value.

Robusta has a set of builtin playbooks.

You can load extra playbook actions in two different ways from git repositories, via HTTPS or via SSH.
For public repos load the playbook via HTTPS, for private repos you will need to use SSH.

1) Loading a git playbook by HTTPS:

.. code-block:: yaml

    playbookRepos:
      # we're adding the robusta chaos-engineering playbooks here from https://github.com/robusta-dev/robusta-chaos
      my_extra_playbooks:
        url: "https://github.com/robusta-dev/robusta-chaos.git"


2) Loading a git playbook by SSH:

.. code-block:: yaml

    playbookRepos:
      # we're adding the robusta chaos-engineering playbooks here
      my_extra_playbooks:
        url: "git@github.com:robusta-dev/robusta-chaos.git"
        key: |-
          -----BEGIN OPENSSH PRIVATE KEY-----
          ewfrcfsfvC1rZXktdjEAAAAABG5vb.....
          -----END OPENSSH PRIVATE KEY-----

The ``key`` should contain a deployment key, with ``read`` access. The ``key`` is required when accessing a git repo via ssh, even for public repositories.

You can also save the SSH key in a `Kubernetes Secret <https://kubernetes.io/docs/concepts/configuration/secret/>`_, and reference it using an environment variable, like this:

.. code-block:: yaml

    additional_env_vars:
     - name: GITHUB_SSH_KEY
       valueFrom:
         secretKeyRef:
           name: ssh-key
           key: id_rsa

    playbookRepos:
      # we're adding the robusta chaos-engineering playbooks here
      my_extra_playbooks:
        url: "git@github.com:robusta-dev/robusta-chaos.git"
        key: "{{env.GITHUB_SSH_KEY}}"

.. note::

    Robusta does not watch for changes on git repositories. Playbooks are loaded from the repository when the server
    starts or the configuration changes, or by running manual reload: ``robusta playbooks reload``

