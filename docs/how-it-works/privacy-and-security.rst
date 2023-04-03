Privacy & Security
############################

Robusta was designed with security in mind. Our four guiding security principles are:

1. **Less is more:** Don't send mountains of observability data when small subsets of the *right* data will do.
2. **Secure by default, configurable if necessary:** Do the right thing for most companies by default. Make it easy for companies with stricter needs to lock-down Robusta further or run it on-prem.
3. **Design for security:** Secure systems are designed to be secure from day one. Discuss security when planning new features.
4. **Experience matters:** Hire engineers who have built secure enterprise platforms before. Make security a core part of company culture.

Data Privacy
********************
The Robusta Open Source doesn't store persistent information itself.
Information is sent to destinations (sinks) like Slack or MSTeams, and they are responsible for storing it.

By default, the following data is sent to sinks. It can be customized if necessary.

- Prometheus alerts
- Alert enrichments, or insights. (Example: an alert for high memory usage will include a memory graph.)
- Technical events from Kubernetes itself. (Example: notifications on crashing pods, K8s warning events.)
- Logs from unhealthy pods. (Note: Robusta does *not* gather logs continuously, rather only from crashing or misbehaving pods.)

SaaS UI
----------
When the Robusta SaaS platform is enabled (optional), it receives the above data, as well as metadata about nodes and workloads in your cluster.
This is used, for example, to show you when deployments were updated and what YAML fields changed.

All data in the SaaS platform is encrypted at rest and stored in accordance with industry standards.

If necessary, the SaaS UI can be run :ref:`on-prem <Self hosted architecture>` as part of our paid plans.

Censoring Logs
********************
Pod logs gathered by Robusta can be censored using regexes.

For example, a payment processing pod might have credit card numbers in its log. These can be sanitized in-cluster.

This feature applies to the following Robusta actions:

- :code:`logs_enricher`
- :code:`report_crash_loop`

To censor logs, define a `python regex <https://www.w3schools.com/python/python_regex.asp>`_ for expressions you wish to filter.

For example:

.. code-block:: yaml

    - logs_enricher:
        regex_replacement_style: SAME_LENGTH_ASTERISKS # You can also use NAMED
        regex_replacer_patterns:
          - name: MySecretPort
              regex: "my secret port \d+"
          - name: UUID
              regex: "[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"

Given the following input:

.. code-block::

    # Input (actual pod log):
    2022-07-28 08:24:45.283 INFO     user's uuid: '193836d9-9cce-4df9-a454-c2edcf2e80e5'
    2022-07-28 08:35:00.762 INFO     Successfully loaded some critical module
    2022-07-28 08:35:01.090 INFO     using my secret port 114, ip: ['172.18.0.3']

The censored output will be:

.. code-block::

    # Output for SAME_LENGTH_ASTERISKS (How it will appear in Slack, for example):

    2022-07-28 08:24:45.283 INFO     user's uuid: '************************************'
    2022-07-28 08:35:00.762 INFO     Successfully loaded some critical module
    2022-07-28 08:35:01.090 INFO     using ******************, ip: ['172.18.0.3']

    # Output for NAMED (How it will appear in Slack, for example):

    2022-07-28 08:24:45.283 INFO     user's uuid: '[UUID]'
    2022-07-28 08:35:00.762 INFO     Successfully loaded some critical module
    2022-07-28 08:35:01.090 INFO     using [MySecretPort], ip: ['172.18.0.3']

It is best to define this in a `global config <https://docs.robusta.dev/master/user-guide/configuration.html#global-config>`_, so it will be applied everywhere.

.. code-block:: yaml

    globalConfig: # Note: no need to specify logs_enricher or report_crash_loop by name here.
      regex_replacement_style: SAME_LENGTH_ASTERISKS
      regex_replacer_patterns:
        - name: MySecretPort
          regex: "my secret port \\d+"
        - name: UUID
          regex: "[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"

Place these values inside Robusta's :code:`generated-values.yaml` file. See `Installation Guide <https://docs.robusta.dev/master/getting-started/installation.html>`_ for more details.
