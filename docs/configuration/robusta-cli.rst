
CLI Commands
##############################

Installing the cli
---------------------
.. tab-set::

    .. tab-item:: PIP
        :name: pip-cli-tab

        .. code-block:: bash
            :name: pip

            pip install -U robusta-cli --no-cache

        .. admonition:: Common Errors
            :class: warning

            * Python 3.7 or higher is required
            * If you are using a system such as macOS that includes both Python 2 and Python 3, run pip3 instead of pip.
            * Errors about *tiller* mean you are running Helm 2, not Helm 3

    .. tab-item:: Docker
        :name: docker-cli-tab

        For **Windows** please use `WSL <https://docs.microsoft.com/en-us/windows/wsl/install>`_.

        * Download robusta script and give it executable permissions:

        .. code-block:: bash
            :name: cb-docker-cli-download-cli-page

            curl -fsSL -o robusta https://docs.robusta.dev/master/_static/robusta
            chmod +x robusta

        * Use the script, for example:

        .. code-block:: bash
            :name: cb-docker-cli-example-cli-page

            ./robusta version

        * In order to upgrade the cli run:

        .. code-block:: bash
            :name: cb-docker-cli-upgrade-cli-page

            ./robusta upgrade-cli

        .. admonition:: Common Errors
            :class: warning

            * Docker daemon is required.

Using the cli
---------------------
The main cli commands are:

``robusta gen-config``
    :ref:`Generate a Helm values file for installing Robusta <Installation>`.

``robusta integrations slack``
    :ref:`Generate a Slack API key for Robusta <Slack>`.

``robusta playbooks trigger``
    :ref:`Manually trigger a playbook <Manual Triggers>`

``robusta playbooks list``
    Show currently configured playbooks.

``robusta playbooks push``
    Push custom playbooks into the current cluster

``robusta playbooks delete``
    Delete custom playbooks from the current cluster

``robusta playbooks list-dirs``
    List current custom playbooks directories in the cluster

``robusta playbooks reload``
    Reload all playbooks in the cluster

``robusta playbooks pull``
    Pull custom playbooks from the current cluster into a local directory

``robusta demo``
    Deploy a crashing pod to Kubernetes to demo Robusta features

``robusta demo-alert``
    Fire an alert on Prometheus AlertManager.

Additional CLI Commands
---------------------------

You can view additional commands with ``robusta --help``.

These two commands are useful for changing Robusta configurations without doing a Helm re-deploy:

``robusta playbooks edit-config``
    Bypass helm and edit Robusta's configuration directly

``robusta playbooks configure``
    Bypass helm and push a new Robusta configuration

.. warning:: Changes made by these commands will be overridden by Helm next time it updates your cluster. Furthermore, the internal Robusta configuration file has a slightly different format than the Helm values.
