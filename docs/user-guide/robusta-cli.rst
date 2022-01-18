CLI Commands
##############################

Installing the cli
---------------------
The robusta cli is installed via pip:

.. code-block::

    pip install robusta-cli

.. warning:: If you are using a system such as macOS that includes both Python 2 and Python 3, run pip3 instead of pip.

Using the cli
---------------------
The main cli commands are:

``robusta gen-config``
    :ref:`Generate a values.yaml file for installing Robusta <Installation Guide>`.

``robusta integrations slack``
    :ref:`Generate a Slack API key for Robusta <Slack>`.

``robusta playbooks trigger``
    :ref:`Manually trigger a playbook <Manual Triggers>`

``robusta playbooks list``
    Show currently configured playbooks.

``robusta playbooks push``
    Push custom playbooks into the current cluster

``robusta playbooks pull``
    Pull custom playbooks from the current cluster into a local directory

``robusta demo``
    Deploy a crashing pod to Kubernetes to demo Robusta features

Additional CLI Commands
---------------------------

You can view additional commands with ``robusta --help``.

These two commands are useful for changing Robusta configurations without doing a Helm re-deploy:

``robusta edit-config``
    Bypass helm and edit Robusta's configuration directly

``robusta playbooks configure``
    Bypass helm and push a new Robusta configuration

.. warning:: Changes made by these commands will be overridden by Helm next time it updates your cluster. Furthermore, the internal Robusta configuration file has a slightly different format than the Helm values.

