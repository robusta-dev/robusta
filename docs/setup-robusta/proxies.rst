Deploying Behind Proxies
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Robusta can run in airgapped environments with no internet access. However, to send notifications to external
:ref:`sinks <Sinks Reference>` like Slack, Robusta might need to communicate with services outside your cluster.

On most clusters this will just work. In clusters behind HTTP(s) proxies, you'll need to configure proxy settings.

Configuring Proxy Settings for Robusta
----------------------------------------
Only the Robusta Runner pod needs proxy settings, as this is the only Pod that communicates with external sinks.

To configure proxy settings, add environment variables using the following Helm values.

* ``runner.additional_env_vars`` - to set one variable at a time
* ``runner.additional_env_froms`` - to set many environment variables at once

Either Helm value can be used, depending on your preference.

For more details, refer to `this GitHub issue about HTTP(s) proxies <https://github.com/robusta-dev/robusta/pull/450>`_.

Domains Used by Robusta Saas UI
---------------------------------
To ensure all Robusta SaaS UI features work well in environments with restricted internet access, please allow access to the following domains.

.. code:: bash

    api.robusta.dev,robusta-charts.storage.googleapis.com,us-central1-docker.pkg.dev,platform.robusta.dev,xvyhpoxfmtpuqqeyqkso.supabase.co,relay.robusta.dev
