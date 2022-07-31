Privacy & Security
############################


Log censoring
********************
In some of the playbooks, like crash reporting, Robusta enriches the message with the pod's logs.

In some cases, this output might contain sensitive data, so a censoring feature was added to Robusta.
The following playbook actions are supported:

- :code:`logs_enricher`
- :code:`report_crash_loop`

To use it, you'll have to define a `python regex <https://www.w3schools.com/python/python_regex.asp>`_ for each expression you wish to filter.
Here is an example configuration, input and output:

Configuration:

.. code-block:: yaml

    - logs_enricher:
      regex_replacement_style: SAME_LENGTH_ASTERISKS # You can also use NAMED
      regex_replacer_patterns:
        - name: MySecretPort
          regex: "my secret port \d+"
        - name: UUID
          regex: "[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"

Input:

.. code-block:: yaml

    # Input (actual pod log):

    2022-07-28 08:24:45.283 INFO     user's uuid: '193836d9-9cce-4df9-a454-c2edcf2e80e5'
    2022-07-28 08:35:00.762 INFO     Successfully loaded some critical module
    2022-07-28 08:35:01.090 INFO     using my secret port 114, ip: ['172.18.0.3']

Output:

.. code-block:: yaml

    # Output for SAME_LENGTH_ASTERISKS (How it will appear in Slack, for example):

    2022-07-28 08:24:45.283 INFO     user's uuid: '************************************'
    2022-07-28 08:35:00.762 INFO     Successfully loaded some critical module
    2022-07-28 08:35:01.090 INFO     using ******************, ip: ['172.18.0.3']

    # Output for NAMED (How it will appear in Slack, for example):

    2022-07-28 08:24:45.283 INFO     user's uuid: '[UUID]'
    2022-07-28 08:35:00.762 INFO     Successfully loaded some critical module
    2022-07-28 08:35:01.090 INFO     using [MySecretPort], ip: ['172.18.0.3']



It is best to define this in a `global config <https://docs.robusta.dev/master/user-guide/configuration.html#global-config>`_, so it will be applied to all the relevant playbooks actions at once:

.. code-block:: yaml

    globalConfig: # Note: no need to specify logs_enricher or report_crash_loop by name here.
      # ...
      regex_replacement_style: SAME_LENGTH_ASTERISKS
      regex_replacer_patterns:
        - name: MySecretPort
          regex: "my secret port \d+"
        - name: UUID
          regex: "[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"

| These values are inside the :code:`generated-values.yaml` file you use when you run :code:`helm install robusta...`
| See `Installation Guide <https://docs.robusta.dev/master/installation.html>`_ for more details.
