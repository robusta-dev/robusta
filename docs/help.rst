:hide-toc:

Getting Support
================

.. toctree::
   :maxdepth: 1
   :hidden:

   docs-contributions

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
contact support@robusta.dev or go to `our slack channel <https://bit.ly/robusta-slack>`_.


.. details:: command not found: robusta (CLI not in path)

    1. Determine where the Robusta-cli binary file is located

    .. code-block:: bash
        :name: cb-find-python-cli-loc

        find / -regex '.*/bin/robusta' 2>/dev/null

    2. Add the path you found (e.g ``/opt/homebrew/bin/``) to your PATH. To do so, find your shell config file ( ~/.profile or ~/.bash_profile or ~/.zshrc etc...) and append the following:

    .. code-block:: bash
        :name: add-path-var

        export PATH="$PATH:<new-path>"

    3. Reopen the terminal or run:

    .. code-block:: bash
        :name: cb-refresh-terminal

        source <your-shell-config-file>

    .. admonition:: Alternative Solution

      Instead of modifying PATH, run Robusta commands via the python3 binary: ``python3 -m robusta.cli.main gen-config``

.. details:: SSL certificate errors on Mac OS

    This implies a python package with certificates is missing on your system.

    To fix it, run ``/Applications/Python 3.9/Install Certificates.command``

    For more info see:
    https://stackoverflow.com/questions/52805115/certificate-verify-failed-unable-to-get-local-issuer-certificate

.. details:: unknown field in com.coreos.monitoring.v1.Prometheus.spec, ValidationError(Prometheus.spec)

    This indicates potential discrepancies between the version of Prometheus you are trying to use and the version of the CRDs in your cluster.

    Follow this guide for :ref:`upgrading CRDs from an older version <Manual Upgrade>`.

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

.. details:: AlertManager Silences are Disappearing

        This happens when AlertManager does not have persistent storage enabled.

        When using Robusta's embedded Prometheus Stack, persistent storage is enabled by default.

        For other Prometheus distributions set the following Helm value (or it's equivalent):

        .. code-block::

                  # this is the setting in in kube-prometheus-stack
                  # the exact setting will differ for other Prometheus distributions
                  alertmanager:
                    alertmanagerSpec:
                      storage:
                        volumeClaimTemplate:
                          spec:
                            accessModes: ["ReadWriteOnce"]
                            resources:
                              requests:
                                storage: 10Gi

Contributing
^^^^^^^^^^^^^^^^^^^^^^

* :ref:`Improving These Docs`
* :ref:`Developing a New Sink`
* :ref:`Developing New Actions`
* :ref:`Build from Source`

More Tutorials
^^^^^^^^^^^^^^^^^^^^^^^
Here are more tutorials from the Robusta community:

.. raw:: html

  <div style="position: relative; height: 0; padding-bottom: 56.25%;"> <iframe src="https://www.youtube.com/embed/2P76WVVua8w" frameborder="0" allowfullscreen style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"></iframe></div>

* **Video:** `Twitter challenge - Robusta.dev on 10 nodes <https://www.youtube.com/watch?v=l_zaCaY_wls>`_ by `Nuno Captain Corsair <https://twitter.com/nunixtech>`_
* `Troubleshoot and automate to fix your k8s Application <https://csaju.com/posts/troubleshoot-and-automate-to-fix-your-k8s-application/>`_ by `Aju Tamang <https://twitter.com/pylang2>`_
* `Getting Started with Robusta on Digital Ocean <https://dev.to/heyrutam/getting-started-with-robusta-on-digital-ocean-3g41>`_ by `Rutam Prita Mishra <https://github.com/Rutam21>`_
* `Getting Started with Robusta on Civo Cloud <https://dev.to/heyrutam/getting-started-with-robusta-on-civo-cloud-5h8f>`_ by `Rutam Prita Mishra <https://github.com/Rutam21>`_
* `Kubernetes troubleshooting and automation using Robusta <https://xxradar.medium.com/kubernetes-troubleshooting-and-automation-using-robusta-13f113fcdc36>`_ by `Philippe Bogaerts <https://twitter.com/xxradar>`_
