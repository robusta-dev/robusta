:hide-navigation:
:hide-toc:

Help
===============

Kubernetes Kommunity
^^^^^^^^^^^^^^^^^^^^

Our free videos on Kubernetes are fairly popular. They are extremely short (under five minutes) and mildly entertaining.

See `Kubernetes Kommunity for details <https://home.robusta.dev/learning/>`_


Here are more tutorials from our awesome community:

Blogs
-----------

* `Troubleshoot and automate to fix your k8s Application <https://csaju.com/blog/troubleshoot-and-automate-to-fix-your-k8s-application/>`_ by `Aju Tamang <https://twitter.com/pylang2>`_
* `Getting Started with Robusta on Digital Ocean <https://dev.to/heyrutam/getting-started-with-robusta-on-digital-ocean-3g41>`_ by `Rutam Prita Mishra <https://github.com/Rutam21>`_
* `Getting Started with Robusta on Civo Cloud <https://dev.to/heyrutam/getting-started-with-robusta-on-civo-cloud-5h8f>`_ by `Rutam Prita Mishra <https://github.com/Rutam21>`_
* `Kubernetes troubleshooting and automation using Robusta <https://xxradar.medium.com/kubernetes-troubleshooting-and-automation-using-robusta-13f113fcdc36>`_ by `Philippe Bogaerts <https://twitter.com/xxradar>`_

Videos
-----------
* `Twitter challenge - Robusta.dev on 10 nodes <https://www.youtube.com/watch?v=l_zaCaY_wls>`_ by `Nuno Captain Corsair <https://twitter.com/nunixtech>`_


Join the conversation
^^^^^^^^^^^^^^^^^^^^^

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
