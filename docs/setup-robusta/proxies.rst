Deploying Behind Proxies
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Robusta can run in airgapped environments with no internet access. However, to send notifications to external
:ref:`sinks <Sinks Reference>` like Slack, Robusta needs to communicate with services outside your cluster.

If your Kubernetes cluster is behind an HTTP proxy or firewall, you will need to configure traffic from Robusta to outside the cluster.

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
