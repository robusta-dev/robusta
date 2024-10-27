Deploying Behind Proxies
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Robusta needs access to the internet if:

* The Robusta UI is enabled (and the SaaS version of the UI is used, not the on-premise version)
* OR Robusta is configured to send notifications to external :ref:`sinks <Sinks Reference>` like Slack

In these cases, you may need to configure your environment to allow traffic from Robusta to outside the cluster. This is usually necessary if your Kubernetes cluster is behind an HTTP proxy or firewall.

Configuring Proxy Settings for Robusta
----------------------------------------

All traffic from Robusta to the external world happens via the robusta-runner deployment. 

To configure proxy settings for robusta-runner, define `HTTP_PROXY` and `HTTPS_PROXY` environment variables with one of the following Helm values:

* ``runner.additional_env_vars`` - to set one variable at a time
* ``runner.additional_env_froms`` - to set many environment variables at once

Either Helm value can be used, depending on your preference. See `this GitHub issue for details and an example configuration <https://github.com/robusta-dev/robusta/pull/450>`_.

Domains Used by Robusta Saas UI
---------------------------------

When using the Robusta SaaS, make sure that access is allowed to the following domains:

.. code:: bash

    api.robusta.dev,robusta-charts.storage.googleapis.com,us-central1-docker.pkg.dev,platform.robusta.dev,xvyhpoxfmtpuqqeyqkso.supabase.co,relay.robusta.dev

Using Robusta in Airgapped Environments or with No External Access
------------------------------------------------------------------------------

You can use Robusta entirely offline if

* No sinks are configured which live on the public internet
* AND the Robusta UI is disabled or running on-premise
