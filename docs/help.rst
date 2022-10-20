:hide-navigation:
:hide-toc:

Help
===============

Ask for help, or just say hi!

1. `Slack <https://bit.ly/robusta-slack>`_ - **link only works on desktop**
2. `GitHub Issues <https://github.com/robusta-dev/robusta/issues>`_

Commercial Support
^^^^^^^^^^^^^^^^^^^
We offer several affordable plans. Contact support@robusta.dev for details. 


Common Errors
^^^^^^^^^^^^^

This list contains some common errors we have encountered over time. If you can't find your answer here,
please contact support@robusta.dev or go to `our slack channel <https://robustacommunity.slack.com/ssb/redirect>`_.


.. details:: Robusta CLI is not in path

    1. Determine where the Robusta-cli binary file is installed  

    .. code-block:: bash
        :name: find-python-bin-loc

        which python3
    
    This <new-path> should be added to the user path directores.

    2. Find your shell config file ( ~/.profile or ~/.bash_profile or ~/.zshrc etc...) and append the following line:

    .. code-block:: bash
        :name: add-path-var

        export PATH="$PATH:<new-path>"

    3. Reopen the terminal or run:

    .. code-block:: bash
        :name: cb-helm-repo-add-show-values

        source <shell-config-file>

    .. note::

      another solution is to run a command (e.g gen-config) directly with python: ``python3 -m robusta.cli.main gen-config``

.. details:: CLI SSL certificate issue

    This error may suggest a python certificate package is missing in your system.
    Try running the script located at:
    /Applications/Python 3.9/Install Certificates.command

    For more info see:
    https://stackoverflow.com/questions/52805115/certificate-verify-failed-unable-to-get-local-issuer-certificate
