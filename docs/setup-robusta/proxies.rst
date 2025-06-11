Deploying Behind Proxies
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Robusta requires internet access in the following cases:

* Robusta SaaS is enabled
* Robusta is configured to send notifications to services such as Slack (via :ref:`sinks <Sinks Reference>`)

If your Kubernetes cluster is behind an HTTP proxy or firewall, follow the instructions below to ensure Robusta and HolmesGPT has the necessary access.

Configuring Proxy Settings for Robusta
----------------------------------------

Outbound traffic from Robusta is handled by the `robusta-runner` deployment.

To configure proxy settings for `robusta-runner`, set the `HTTP_PROXY` and `HTTPS_PROXY` environment variables. You can do so with one of the following Helm values:

* ``runner.additional_env_vars`` - to set one environment variable at a time
* ``runner.additional_env_froms`` - to set many environment variables at once

Configuring Proxy Settings for HolmesGPT
----------------------------------------

Set the `HTTP_PROXY` and `HTTPS_PROXY` environment variables. You can do so with the following Helm values:

* ``holmes.additionalEnvVars`` - to set one environment variable at a time

Either Helm value can be used, depending on your preference. See `this GitHub issue for details and an example configuration <https://github.com/robusta-dev/robusta/pull/450>`_.

Domains Used by Robusta Saas UI
---------------------------------

If you are using Robusta SaaS, ensure that your network allows access to the following domains:

.. code:: bash

    api.robusta.dev,robusta-charts.storage.googleapis.com,us-central1-docker.pkg.dev,platform.robusta.dev,xvyhpoxfmtpuqqeyqkso.supabase.co,relay.robusta.dev,sp.robusta.dev

Running Robusta in Air-Gapped or Offline Environments
------------------------------------------------------------------------------

You can run Robusta entirely offline if the following conditions are met:

* No external sinks are configured (e.g., services on the public internet).
* The Robusta UI is either disabled or running on-premise.
