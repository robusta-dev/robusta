Two-way Interactivity
^^^^^^^^^^^^^^^^^^^^^^^^^

Two-way interactivity allows the Robusta UI and the Slack sink to connect to the Robusta running in your cluster.

The Robusta UI uses interactivity to display dynamic data, such as Prometheus graphs.
Slack uses it to support custom remediation buttons.

To **enable** interactivity, set the following in your `generated_values.yaml` file:

.. code-block:: yaml

    disableCloudRouting: false

See also
------------------------------

* :ref:`Robusta architecture <Architecture>`