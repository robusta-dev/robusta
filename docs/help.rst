:hide-navigation:
:hide-toc:

Help
===============

Ask for help, or just say hi!

.. grid:: 5
   :gutter: 3

   .. grid-item-card:: :octicon:`comment-discussion;1em;` Slack    
      :class-card: sd-bg-light sd-bg-text-light
      :link: https://bit.ly/robusta-slack


   .. grid-item-card:: :octicon:`mark-github;1em;` Github Issue
      :class-card: sd-bg-light sd-bg-text-light
      :link: https://github.com/robusta-dev/robusta/issues

Commercial Support
^^^^^^^^^^^^^^^^^^^
Contact support@robusta.dev for details. 


Common Errors
^^^^^^^^^^^^^

This list contains some common errors we have encountered over time. If you can't find your answer here,
please contact support@robusta.dev or go to `our slack channel <https://bit.ly/robusta-slack>`_.


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

      If you prefer not to update PATH, you can use Python's ``-m`` flag

      ``python3 -m robusta.cli.main gen-config``

.. details:: SSL certificate issues on Mac OS when using the cli

    This implies a python package with certificates is missing on your system.

    To fix it, run ``/Applications/Python 3.9/Install Certificates.command``

    For more info see:
    https://stackoverflow.com/questions/52805115/certificate-verify-failed-unable-to-get-local-issuer-certificate

More Tutorials
^^^^^^^^^^^^^^^^^^^^^^^
Here are more tutorials from the Robusta community:

* **Video:** `Kubernetes Notifications, Troubleshooting, And Automation With Robusta <https://www.youtube.com/watch?v=2P76WVVua8w>`_ by Viktor Farcic
* **Video:** `Twitter challenge - Robusta.dev on 10 nodes <https://www.youtube.com/watch?v=l_zaCaY_wls>`_ by `Nuno Captain Corsair <https://twitter.com/nunixtech>`_
* `Troubleshoot and automate to fix your k8s Application <https://csaju.com/blog/troubleshoot-and-automate-to-fix-your-k8s-application/>`_ by `Aju Tamang <https://twitter.com/pylang2>`_
* `Getting Started with Robusta on Digital Ocean <https://dev.to/heyrutam/getting-started-with-robusta-on-digital-ocean-3g41>`_ by `Rutam Prita Mishra <https://github.com/Rutam21>`_
* `Getting Started with Robusta on Civo Cloud <https://dev.to/heyrutam/getting-started-with-robusta-on-civo-cloud-5h8f>`_ by `Rutam Prita Mishra <https://github.com/Rutam21>`_
* `Kubernetes troubleshooting and automation using Robusta <https://xxradar.medium.com/kubernetes-troubleshooting-and-automation-using-robusta-13f113fcdc36>`_ by `Philippe Bogaerts <https://twitter.com/xxradar>`_
