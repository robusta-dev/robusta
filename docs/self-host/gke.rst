Deploying to Google Cloud Platform
##################################

Prerequisites
------------------------------
To follow the installation, make sure you have:

* `Helm 3 <https://helm.sh/docs/intro/install/>`_ 
* :ref:`Robusta CLI <CLI Commands>`
* `Google Cloud CLI <https://cloud.google.com/sdk/docs/install-sdk>`_

Minimal installation
------------------------------

1. Set up a GKE global static IP 
---------------------------------

.. code-block:: bash
   :name: gke-create-static-global-ip

    gcloud compute addresses create robusta-platform-ip --global
   
.. admonition:: Common Errors
   :class: warning

   * Make sure to use --project=<your-project-id> if its not set on your workspace.
   * This must be a Global IP address.

2. Set up DNS
--------------
in this step we are going to route your DNS to the GKE global static IP.

* find the gloabl robusta-platform-ip address:

.. code-block:: bash
    :name: gke-get-global-ip-address

    gcloud compute addresses list --filter=name:robusta-platform-ip --global 

Route the subdomains
^^^^^^^^^^^^^^^^^^^^^

The linking process depends on your domain provider (e.g. Namecheap, GoDaddy or Google Domains). 
Usually it involves creating an “A Record”.
**(replace my-website.com with your domain)**

1. db.robusta.my-website.com
2. platform.robusta.my-website.com
3. relay.robusta.my-website.com
4. api.robusta.my-website.com

DNS Troubleshooting
^^^^^^^^^^^^^^^^^^^

| To validate the routing, ping the sub-domains and make sure you see the GKE global static IP.
| For example:

.. code-block:: bash
    :name: gke-validate-dns

    ping platform.robusta.my-website.com

3. Generate the self host values files
---------------------------------------
**make sure to use robusta.my-website.com as domain**

.. code-block:: bash
    :name: gke-gen-config

    robusta self-host gen-config --provider gke --domain <domain>


You can now install the minimal Robusta platform into your cluster using:
    
.. code-block:: bash
    :name: install

    helm install robusta-platform robusta-platform/robusta-platform -f values.yaml


4. integartions
----------------

Now that your values file is ready, here are a couple of guides we'd recommend you check out.

* `Google SSO integration <https://helm.sh/docs/intro/install/>`_
* `Azure SSO integartion <https://helm.sh/docs/intro/install/>`_
* `Slack integration <https://helm.sh/docs/intro/install/>`_



Troubleshooting
---------------