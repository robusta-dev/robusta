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
        # branch: some_branch    # optional: which git branch to install from
        # pip_install: True      # optional: load this playbook's dependencies (default True)

Loading Actions from Private Git Repos
-----------------------------------------

For private repos, load actions using SSH not HTTPs.

This method works for public repos too:

.. code-block:: yaml

    playbookRepos:
      # add the same playbooks as above, this time over ssh
      my_extra_playbooks:
        url: "git@github.com:robusta-dev/robusta-chaos.git"
        key: LS0tLS1CRUdJTiBPUEVOU1NIIFBSSVZBVEUgS0VZLS0tL
        # branch: some_branch    # optional: which git branch to install from
        # pip_install: True      # optional: load this playbook's dependencies (default True)


The ``key`` parameter must contain a ``base64`` encoded deployment key with ``read`` access.

.. admonition:: Example deployment key

     .. code-block:: yaml

        -----BEGIN OPENSSH PRIVATE KEY-----
        ewfrcfsfvC1rZXktdjEAAAAABG5vb.....
        -----END OPENSSH PRIVATE KEY-----


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

Baking Actions into a Custom Image
--------------------------------------

By default, Robusta loads custom actions at runtime. You can also bake custom actions into Robusta at build time. To do so:

1. Create a custom image that inherits from the robusta-runner image. Copy your actions into the image and install them into site-packages with all dependencies.

.. code-block::

    COPY my_playbooks/ /etc/robusta/playbooks/my_playbooks
    RUN python3 -m pip install --no-cache-dir /etc/robusta/playbooks/my_playbooks

2. Load your actions with a ``file:///`` url and ``pip_install: False``.

.. code-block:: yaml

    playbookRepos:
      my_extra_playbooks:
        url: "file:///etc/robusta/playbooks/my_playbooks"
        pip_install: False

3. Configure Robusta's Helm value to use your custom image.
