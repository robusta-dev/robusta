Common Errors
######################

This list contains some common errors we have encountered over time. If you can't find your answer here,
please contact support@robusta.dev or go to `our slack channel <https://robustacommunity.slack.com/ssb/redirect>`_.


.. dropdown:: command not found: robusta (Robusta CLI is not in path)
    :color: light

    1. Determine where the Robusta-cli binary file is located  

    .. code-block:: bash
        :name: cb-find-python-cli-loc

        find / -regex '.*/bin/robusta' 2>/dev/null
    
    2. Add the found path ``.../bin/`` (E.g ``/opt/homebrew/bin/``) to the user path directories. 

    * Find your shell config file ( ~/.profile or ~/.bash_profile or ~/.zshrc etc...)

    * Append the following line to the shell config file:

    .. code-block:: bash
        :name: add-path-var

        export PATH="$PATH:<new-path>"

    3. Reopen the terminal or run:

    .. code-block:: bash
        :name: cb-refresh-terminal

        source <your-shell-config-file>

    .. note::

      another solution is to run a command (e.g gen-config) directly with python: ``python3 -m robusta.cli.main gen-config``

.. dropdown:: CLI SSL certificate issue
    :color: light

    This error may suggest a python certificate package is missing in your system.
    Try running the script located at:
    /Applications/Python 3.9/Install Certificates.command

    For more info see:
    https://stackoverflow.com/questions/52805115/certificate-verify-failed-unable-to-get-local-issuer-certificate
