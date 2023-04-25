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
    
    This <new-path> should be added to the user path directories.

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

.. details:: SSL certificate errors on Mac OS

    This implies a python package with certificates is missing on your system.

    To fix it, run ``/Applications/Python 3.9/Install Certificates.command``

    For more info see:
    https://stackoverflow.com/questions/52805115/certificate-verify-failed-unable-to-get-local-issuer-certificate

.. details:: robusta-runner isn't working or has exceptions

    Check the pod's memory consumption. If necessary, increase the memory request in the Helm values:

    .. code-block:: yaml

        runner:
          resources:
            requests:
              memory: 2048Mi
            limits:
              memory: 2048Mi

    Here's a representative error caused by too little memory:

    .. details:: Discovery Error

        .. code-block::

            2023-04-17 23:37:43.019 ERROR    Discovery process internal error
            2023-04-17 23:37:43.022 INFO     Initialized new discovery pool
            2023-04-17 23:37:43.022 ERROR    Failed to run publish discovery for robusta_ui_sink
            Traceback (most recent call last):
              File "/app/src/robusta/core/sinks/robusta/robusta_sink.py", line 175, in __discover_resources
                results: DiscoveryResults = Discovery.discover_resources()
              File "/app/src/robusta/core/discovery/discovery.py", line 288, in discover_resources
                raise e
              File "/app/src/robusta/core/discovery/discovery.py", line 280, in discover_resources
                return future.result()
              File "/usr/local/lib/python3.9/concurrent/futures/_base.py", line 446, in result
                return self.__get_result()
              File "/usr/local/lib/python3.9/concurrent/futures/_base.py", line 391, in __get_result
                raise self._exception
            concurrent.futures.process.BrokenProcessPool: A process in the process pool was terminated abruptly while the future was running or pending.


More Tutorials
^^^^^^^^^^^^^^^^^^^^^^^
Here are more tutorials from the Robusta community:

* **Video:** `Kubernetes Notifications, Troubleshooting, And Automation With Robusta <https://www.youtube.com/watch?v=2P76WVVua8w>`_ by Viktor Farcic
* **Video:** `Twitter challenge - Robusta.dev on 10 nodes <https://www.youtube.com/watch?v=l_zaCaY_wls>`_ by `Nuno Captain Corsair <https://twitter.com/nunixtech>`_
* `Troubleshoot and automate to fix your k8s Application <https://csaju.com/blog/troubleshoot-and-automate-to-fix-your-k8s-application/>`_ by `Aju Tamang <https://twitter.com/pylang2>`_
* `Getting Started with Robusta on Digital Ocean <https://dev.to/heyrutam/getting-started-with-robusta-on-digital-ocean-3g41>`_ by `Rutam Prita Mishra <https://github.com/Rutam21>`_
* `Getting Started with Robusta on Civo Cloud <https://dev.to/heyrutam/getting-started-with-robusta-on-civo-cloud-5h8f>`_ by `Rutam Prita Mishra <https://github.com/Rutam21>`_
* `Kubernetes troubleshooting and automation using Robusta <https://xxradar.medium.com/kubernetes-troubleshooting-and-automation-using-robusta-13f113fcdc36>`_ by `Philippe Bogaerts <https://twitter.com/xxradar>`_
