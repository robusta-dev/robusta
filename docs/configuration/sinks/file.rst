File
###########

.. admonition:: This page documents a legacy sink in Robusta classic
   :class: warning

   For new setups, we recommend `HolmesGPT <https://holmesgpt.dev/>`_ instead.

   Sinks statically forward every notification to a fixed destination. Modern Robusta instead investigates and routes alerts **agentically** so the LLM makes intelligent triage decisions about each alert. Set this up with `Alerts Triage <https://platform.robusta.dev/holmes/alerts-triage>`_ for alerts, or :ref:`Triggered Workflows <defining-playbooks>` for custom events.


Robusta can write issues and events in your Kubernetes cluster to a local file (in JSON format).


.. admonition:: Add this to your generated_values.yaml

    .. code-block:: yaml

        sinksConfig:
        - file_sink:
            name: file_sink
            file_name: optional\path\to\file.json

The ``file_name`` is the path to the output file where the playbook finding data will be written.
It has to be a valid path with write permissions. This parameter is optional.
If you omit it the stdout (console) will be used as default output.

Save the file and run

.. code-block:: bash
   :name: cb-add-webhook-sink

    helm upgrade robusta robusta/robusta --values=generated_values.yaml
