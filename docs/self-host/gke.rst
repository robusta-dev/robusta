Deploying to Google Cloud Platform
##################################

Prerequisites
---------------

To follow the installation, make sure you have:

* `Helm 3 <https://helm.sh/docs/intro/install/>`_ 
* :ref:`Robusta CLI <CLI Commands>`
* `Google Cloud CLI <https://cloud.google.com/sdk/docs/install-sdk>`_

GCP Guide
------------------------------

Set up a GKE global static IP 
---------------------------------

* Locate your `project ID <https://support.google.com/googleapi/answer/7014113?hl=en>`_ if its not set on your workspace.

* Create a new global IP:

.. code-block:: bash
   :name: cb-gke-create-static-global-ip

    gcloud compute addresses create robusta-platform-ip --global --project=<your-project-id>
   
.. admonition:: Common Errors
   :class: warning

   * Make sure to use --project=<your-project-id> if its not set on your workspace.
   * This must be a Global IP address.

Set up DNS
--------------
in this step we are going to route your DNS to the GKE global static IP.

* find the gloabl robusta-platform-ip address:

.. code-block:: bash
    :name: cb-gke-get-global-ip-address

    gcloud compute addresses list --filter=name:robusta-platform-ip --global --project=<your-project-id>

Route the subdomains to the new IP
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The linking process depends on your domain provider (e.g. Namecheap, GoDaddy or Google Domains). 
Usually it involves creating an “A Record”.
**(replace MY_DOMAIN with your domain)**

1. db.MY_DOMAIN
2. platform.MY_DOMAIN
3. relay.MY_DOMAIN
4. api.MY_DOMAIN

DNS Troubleshooting
^^^^^^^^^^^^^^^^^^^^

| To validate the routing, ping the sub-domains and make sure you see the GKE global static IP.
| For example:

.. code-block:: bash
    :name: cb-gke-validate-dns

    ping platform.MY_DOMAIN

Generate the self host values files
---------------------------------------
**make sure to use MY_DOMAIN as domain**

.. code-block:: bash
    :name: cb-gke-gen-config

    robusta self-host gen-config --provider gke --domain <MY_DOMAIN>

Deploy
--------

* Add the chart repository:

.. code-block:: bash
    :name: cb-gke-add-helm-repo

    helm repo add robusta-platform https://robusta-charts-all.storage.googleapis.com && helm repo update

* Install the Robusta platform into your cluster using `Helm <https://helm.sh/docs/intro/install/>`_ :
    
.. code-block:: bash
    :name: cb-gke-install

    helm install robusta-platform robusta-platform/robusta-platform -f self_host_values.yaml

**It will take the Robusta platform approximately 30 min to activate due to Google's SSL certificate provisioning process.**
check the :ref:`Troubleshooting <Troubleshooting>` section for more info.

Configure Robusta CLI to use your backend configuration.
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

robusta_cli_config.json file was generated for you with the required settings.

* Add an environment variable that points to the config file:
.. code-block:: bash
    :name: cb-gke-add-env-var-backend-config

    export ROBUSTA_BACKEND_PROFILE=/Path/to/your/robusta_cli_config.json

* verify that Robusta CLI uses your backend configuration, run:
.. code-block:: console
    :name: cb-gke-verify-cli-backend-config

    $ robusta version
    Using Robusta backend profile: /Path/to/your/robusta_cli_config.json

Integrations
----------------

Now that your values file is ready, here are a couple of guides we'd recommend you check out.

* :ref:`Google SSO integration <Login With Google>`
* :ref:`Slack integration <Create a Slack application>`

Troubleshooting
----------------

GKE Managed certificate 
^^^^^^^^^^^^^^^^^^^^^^^^

Robusta's platform uses Google-managed SSL certificate which takes approximately 30~ min to activate. 

* Go to `GKE Managed certificates <https://console.cloud.google.com/net-services/loadbalancing/advanced/sslCertificates/list>`_ and find ``robusta-platform-certificate``.
* Make sure the certificate Status is Active and you see your 4 sub-domains with an Active status as well.

Load balancer
^^^^^^^^^^^^^^^
The load balancer depends on the managed certificate to run proprly.

* Go to `GKE Load Balancers <https://console.cloud.google.com/net-services/loadbalancing/list/loadBalancers/>`_ find the ``robusta-platform-ingress`` load balacer.
* Make sure there are 5 backend services running with green check mark.

Deployments
^^^^^^^^^^^^^
Run:

.. code-block:: bash
    :name: cb-self-host-gke-check-deployments

    kubectl get deploy

Make sure ``robusta-ui``, ``platform-relay``, ``kong``, ``auth``, ``meta`` and ``rest`` are in running state.

Login to the UI
^^^^^^^^^^^^^^^^

Go to ``https://platform.MY_DOMAIN`` and sign up. Then try to log in.

Support
^^^^^^^^^^^^^^^

For further help contact us on `Slack <https://bit.ly/robusta-slack>`_ or `support@robusta.dev <mailto:support@robusta.dev>`_