Deploying to self managed cluster
##################################

Prerequisites
------------------------------

To follow the installation, make sure you have:

* `Helm 3 <https://helm.sh/docs/intro/install/>`_ 
* :ref:`Robusta CLI <CLI Commands>`

Minimal installation
------------------------------

Set up DNS to Node Ports
-------------------------

In this step we are going to route your DNS to the Robusta platform Node port services.


The linking process depends on your domain provider (e.g. Namecheap, GoDaddy or Google Domains). 
Usually it involves creating an “A Record”.
**(replace MY_DOMAIN with your domain)**

1. db.MY_DOMAIN
2. platform.MY_DOMAIN
3. relay.MY_DOMAIN
4. api.MY_DOMAIN

Generate the self host values files
---------------------------------------
**make sure to use MY_DOMAIN as domain**

.. code-block:: bash
    :name: gke-gen-config

    robusta self-host gen-config --domain <MY_DOMAIN>

Configure Robusta CLI to use your backend configuration.
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

robusta_cli_config.json file was generated for you with the required settings.

* Add an environment variable that points to the config file:
.. code-block:: bash
    :name: add-env-var-backend-config

    export ROBUSTA_BACKEND_PROFILE=/Path/to/your/robusta_cli_config.json

* verify that Robusta CLI uses your backend configuration, run:
.. code-block:: console
    :name: verify-cli-backend-config

    $ robusta version
    Using Robusta backend profile: /Path/to/your/robusta_cli_config.json

Deploy
--------

You can now install the Robusta platform into your cluster using `Helm <https://helm.sh/docs/intro/install/>`_ :
    
.. code-block:: bash
    :name: install

    helm install robusta-platform robusta-platform/robusta-platform -f values.yaml

**It will take the Robusta platform approximately 30~ min to activate due to GKE Google-managed SSL certificate.**
check the :ref:`Troubleshooting <Troubleshooting>` section for more info.

Integartions
----------------

Now that your values file is ready, here are a couple of guides we'd recommend you check out.

* `Google SSO integration <https://helm.sh/docs/intro/install/>`_
* `Slack integration <https://helm.sh/docs/intro/install/>`_

Troubleshooting
---------------

Deployments
^^^^^^^^^^^^^

run:

.. code-block:: bash
    :name: self-host-gke-check-deployments

    kubectl get deploy

make sure ``robusta-ui``, ``platform-relay``, ``kong``, ``auth``, ``meta`` and ``rest`` are in running state.

Login to the UI
^^^^^^^^^^^^^^^

go to ``https://platform.MY_DOMAIN`` and sign up. Then try to log in.

Support
^^^^^^^^^^^^^^^

for further help contact us on `Slack <https://join.slack.com/t/robustacommunity/shared_invite/zt-10rkepc5s-FnXKvGjrBmiTkKdrgDr~wg>`_ or `support@robusta.dev <mailto:support@robusta.dev>`_