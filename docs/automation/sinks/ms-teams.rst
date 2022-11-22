MS teams
##########

Robusta can send playbook result to a MS teams channel webhook.

To configure a MS teams sink we need a webhook URL for the target teams channel. You can configure it in MS teams channel connectors.

Configuring the MS teams sink
------------------------------------------------

.. admonition:: Add this to your generated_values.yaml

    .. code-block:: yaml

        sinks_config:
        - ms_teams_sink:
            name: main_ms_teams_sink
            webhook_url: teams channel incoming webhook  # see video below

Save the file and run

.. code-block:: bash
   :name: cb-add-msteams-sink

    helm upgrade robusta robusta/robusta --values=generated_values.yaml

**Example Output:**

    .. image:: /images/deployment-babysitter-teams.png
      :width: 600
      :align: center

Creating a webhook url in MS Teams
-----------------------------------
MS Teams isn't the most intuitive, so we've created a video on getting the ``webhook_url`` parameter from MS Teams itself:

.. raw:: html

    <div style="position: relative; padding-bottom: 56.25%; height: 0;"><iframe src="https://www.loom.com/embed/4edd6506369041e08016329fe92e7720" frameborder="0" webkitallowfullscreen mozallowfullscreen allowfullscreen style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"></iframe></div>
