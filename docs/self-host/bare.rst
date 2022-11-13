Deploying to self managed cluster
##################################

Prerequisites
------------------------------

To follow the installation, make sure you have:

* `Helm 3 <https://helm.sh/docs/intro/install/>`_ 
* :ref:`Robusta CLI <CLI Commands>`

Installation
-------------

In this guide we are going to deploy the Robusta platform into your cluster.
We will then set DNS to the Robusta platform NodePort Services.  

Generate the self host values files
---------------------------------------
**make sure to use MY_DOMAIN as domain**

.. code-block:: bash
    :name: cb-self-managed-gen-config

    robusta self-host gen-config --domain <MY_DOMAIN>

Deploy
--------

You can now install the Robusta platform into your cluster using `Helm <https://helm.sh/docs/intro/install/>`_ :
    
.. code-block:: bash
    :name: cb-self-managed-install

    helm install robusta-platform robusta-platform/robusta-platform -f values.yaml

Set up DNS to NodePorts
-------------------------

In this step we are going to route your DNS to the Robusta platform NodePort services.
NodePorts are in the 30000-32767 range usually. First, get the node ports:

.. code-block:: bash
    :name: cb-self-managed-get-node-ports

    kubectl get svc robusta-ui kong platform-relay platform-relay-ws

route each subdomain to ExposedIP:NodePort for the following services:

1. db.MY_DOMAIN -> ``kong``
2. platform.MY_DOMAIN -> ``robusta-ui``
3. relay.MY_DOMAIN -> ``platform-relay-ws``
4. api.MY_DOMAIN -> ``platform-relay``

Configure the Robusta CLI to use your backend configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

robusta_cli_config.json file was generated for you with the required settings.

* Add an environment variable that points to the config file:
.. code-block:: bash
    :name: cb-self-managed-add-env-var-backend-config

    export ROBUSTA_BACKEND_PROFILE=/Path/to/your/robusta_cli_config.json

* verify that the Robusta CLI uses your backend configuration, run:
.. code-block:: console
    :name: cb-self-managed-verify-cli-backend-config

    $ robusta version
    Using Robusta backend profile: /Path/to/your/robusta_cli_config.json

DNS Troubleshooting
^^^^^^^^^^^^^^^^^^^

| To validate the routing, ping the sub-domains and make sure you see the expected ip address.
| For example:

.. code-block:: bash
    :name: cb-self-managed-validate-dns

    ping platform.MY_DOMAIN

Once the subdomains are active consult :ref:`Troubleshooting <Troubleshooting>` to make sure everythings works.

Integartions
--------------

Here are a couple of guides we'd recommend you check out.

* :ref:`Google SSO integration <Login With Google>`
* :ref:`Slack integration <Create a Slack application>`

Troubleshooting
---------------

Deployments
^^^^^^^^^^^^

Run:

.. code-block:: bash
    :name: cb-self-managed-check-deployments

    kubectl get deploy

Make sure ``robusta-ui``, ``platform-relay``, ``kong``, ``auth``, ``meta`` and ``rest`` are in running state.

Login to the UI
^^^^^^^^^^^^^^^^

Go to ``https://platform.MY_DOMAIN`` and sign up. Then try to log in.

Support
^^^^^^^^^^^^^^^^

For further help contact us on `Slack <https://bit.ly/robusta-slack>`_ or `support@robusta.dev <mailto:support@robusta.dev>`_