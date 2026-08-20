Privacy and Security
############################

Robusta was designed with security in mind. Our four guiding security principles are:

1. **Less is more:** Don't send mountains of observability data when small subsets of the *right* data will do.
2. **Secure by default, configurable if necessary:** Do the right thing for most companies by default. Make it easy for companies with stricter compliance needs to lock-down Robusta further or run it on-prem.
3. **Design for security:** Secure systems are designed to be secure from day one. Discuss security when planning new features.
4. **Experience matters:** Hire engineers who have built secure enterprise platforms before. Make security a core part of company culture.

Running Robusta in Airgapped Environments
******************************************
Refer to :ref:`Deploying Behind Proxies`.

To run the Robusta UI on premise, :ref:`speak to our team <Getting Support>`.

Handling Secrets in Robusta's Helm Values
******************************************
Refer to :ref:`Managing Secrets`.

Runner Pod Security
******************************************

By default, the Robusta runner pod runs as a non-root user (uid 1000) with all Linux capabilities dropped,
``seccompProfile: RuntimeDefault`` and privilege escalation disabled.

The runner container's root filesystem is also mounted read-only, with writable ``emptyDir`` volumes only
where the runner needs to write at runtime (``/tmp``, git playbook clones, pip caches and runtime-installed
Python packages). This is controlled by the ``runner.hardenedFs`` Helm value (default ``true``). Setting it
to ``false`` keeps a writable root filesystem while still running as non-root. An explicit
``runner.securityContext.container.readOnlyRootFilesystem`` value always takes precedence over ``hardenedFs``.

.. note::

    With the read-only filesystem enabled, external playbook packages that declare ``console_scripts``
    entry points cannot be pip-installed at runtime. Refer to :ref:`Loading External Actions`.

Limiting Robusta's Access in Your Cluster
*******************************************

To reduce the permissions that Robusta needs in your cluster:

- On OpenShift you can deploy Robusta with a limited SCC - refer to :ref:`OpenShift`

To further limit Robusta's permissions, :ref:`speak to our team for guidance <Getting Support>`.
