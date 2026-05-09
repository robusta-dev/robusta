Deploying Behind Proxies
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If your Kubernetes cluster is behind an HTTP proxy or firewall, follow the instructions below to ensure Robusta and HolmesGPT has the necessary access.

Configuring Proxy Settings
----------------------------------------

Set the ``HTTP_PROXY`` and ``HTTPS_PROXY`` environment variables in your Helm values:

.. code-block:: yaml

    runner:
      additional_env_vars:
        - name: HTTP_PROXY
          value: "http://your-proxy:port"
        - name: HTTPS_PROXY
          value: "http://your-proxy:port"

    holmes:
      additionalEnvVars:
        - name: HTTP_PROXY
          value: "http://your-proxy:port"
        - name: HTTPS_PROXY
          value: "http://your-proxy:port"

To set many variables at once, ``runner.additional_env_froms`` accepts a Kubernetes ``envFrom`` source. See `this GitHub issue <https://github.com/robusta-dev/robusta/pull/450>`_ for details and examples.

Domains Used by Robusta Saas UI
---------------------------------

If you are using Robusta SaaS, ensure that your network allows access to the following domains:

.. code:: bash

    api.robusta.dev,robusta-charts.storage.googleapis.com,us-central1-docker.pkg.dev,platform.robusta.dev,xvyhpoxfmtpuqqeyqkso.supabase.co,relay.robusta.dev,sp.robusta.dev

Running Robusta in Air-Gapped or Offline Environments
------------------------------------------------------------------------------

Contact support@robusta.dev for self-hosted deployment options that work in air-gapped or offline environments.
