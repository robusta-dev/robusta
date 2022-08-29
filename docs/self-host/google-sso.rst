Login With Google
#########################

Prerequisites
---------------

To follow the integration guide, make sure you have:

* Google cloud project. Consult `manage projects <https://cloud.google.com/resource-manager/docs/creating-managing-projects>`_ if you dont have one.
* self_host_values.yaml file

Integration
----------------

To enable Google Authentication in the Robusta UI, you need to set up a Google OAuth application and add the application credentials to your self_host_values.yaml file.

Creae the OAuth consent screen
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

#. Go to `OAuth consent screen <https://console.cloud.google.com/apis/credentials/consent>`_ . Make sure you are in the right project.
#. On the OAuth consent screen page select ``External`` .
#. Fill the following:

   * App name (e.g My-Organization-Robusta).

   * User support email (can be your email).

   * Under Authorized domains add your DOMAIN, remove any subdomains like “robusta.DOMAIN”.

   * Developer contact information (can be your email).

#. Click ``Save`` .

Create Credentials 
^^^^^^^^^^^^^^^^^^^^^^

#. Go to `Credentials <https://console.cloud.google.com/apis/credentials>`_ . Make sure its your project.
#. Click ``+ Create Credentials`` -> ``OAuth Client IDs`` .
#. For application type choose ``web application page`` .
#. Insert your app name (e.g My-Organization-Robusta)
#. Add Authorized redirect URIs: ``https://db.MY_DOMAIN/auth/v1/callback`` . use DOMAIN from your self_host_values.yaml file.
#. Click ``Create`` .
#. Save your ``Client ID`` and ``Client Secret`` .

Adjust self_host_values.yaml file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Fill ``Client ID`` and ``Client Secret`` from the previous step and add the following lines to your self_host_values.yaml file.

.. code-block:: bash
   :name: cb-google-sso-yaml-values

    ENABLE_GOOGLE_SIGNUP: true
    GOOGLE_CLIENT_ID: <your-client-id>
    GOOGLE_CLIENT_SECRET: <your-client-secret>

Support
^^^^^^^^^^^^^^^

For further help contact us on `Slack <https://join.slack.com/t/robustacommunity/shared_invite/zt-10rkepc5s-FnXKvGjrBmiTkKdrgDr~wg>`_ or `support@robusta.dev <mailto:support@robusta.dev>`_