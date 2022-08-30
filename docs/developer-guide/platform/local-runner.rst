Running Robusta Locally
################################

Prerequisites
---------------

To follow the guide

* Run a local cluster using `Kind <https://kind.sigs.k8s.io/docs/user/quick-start/>`_  or `minikube <https://minikube.sigs.k8s.io/docs/start/>`_.

Setting Up Robusta playbooks
------------------------------

Inside the Robutsa repo folder create the following file hierarchy:

.. code-block:: bash
   :name: cb-robusta-local-playbooks-file-hierarchy

    robusta
    ├── deployment
        ├── defaults
        │   ├── pyproject.toml
        │   └── robusta_playbooks


#. Under ``deployments`` create  ``defaults`` folder.
#. Copy the ``robusta_plabyooks`` folder and the ``pyproject.toml`` file from the ``playbooks`` folder in the repo.
#. Install the robusta_playbooks for the local project. Inside the defaults folder, run:

Get the playbooks_config file
------------------------------

To simulate in cluster environment, we will use the config file from a running Robusta instance.

* Get an interactive shell to your runner using: 

.. code-block:: bash
   :name: cb-robusta-local-connect-to-runner

    kubectl exec -it deployment/robusta-runner -- /bin/sh    

* Print the configuration file:

.. code-block:: bash
   :name: cb-robusta-local-print-config

    cd /etc/robusta/config && cat active_playbooks.yaml   

* Copy the file to a new ``active_playbooks.yaml`` file under ``deployment`` folder

.. code-block:: bash
   :name: cb-robusta-local-config-file-hierarchy

    robusta
    ├── deployment
        ├── active_playbooks.yaml   

Setting Up The Project 
-----------------------

Environment Variables
^^^^^^^^^^^^^^^^^^^^^^^^^

Add the following environment variables to your IDE or system.

adjust ``PLAYBOOKS_CONFIG_FILE_PATH`` and ``PLAYBOOKS_ROOT``

.. code-block:: json
   :name: cb-robusta-local-dev-env-vars

    "INSTALLATION_NAMESPACE": "default"
    "PLAYBOOKS_CONFIG_FILE_PATH": "<path>/robusta/deployment/active_playbooks.yaml",
    "ENABLE_MANHOLE": "false",
    "ENABLE_COLORED_LOGS" : "true",
    "PROMETHEUS_ENABLED": "true",
    "LOG_LEVEL": "INFO",
    "CLOUD_ROUTING": "false",
    "RUNNER_VERSION": "0.0.0",
    "RELAY_EXTERNAL_ACTIONS_URL" : "https://api.robusta.dev/integrations/generic/actions",
    "WEBSOCKET_RELAY_ADDRESS": "wss://relay.robusta.dev",
    "ROBUSTA_UI_DOMAIN" : "https://platform.robusta.dev",
    "ROBUSTA_TELEMETRY_ENDPOINT" : "https://api.robusta.dev/telemetry",
    "PLAYBOOKS_ROOT": "<path>/robusta/deployment",

Project Settings
^^^^^^^^^^^^^^^^^^^^^

Set up the python project to run as a module instead of a file.

.. tab-set::

    .. tab-item:: VS code
        :name: robusta-local-vscode

        In your ``launch.json`` instead of ``"program": "${file}"`` use ``"module": "robusta.runner.main"`` 
        to run the project as a module.

    .. tab-item:: Pycharm
        :name: robusta-local-pychram

        Inside project configuration -> interpreter options use: ``-m robusta.runner.main``