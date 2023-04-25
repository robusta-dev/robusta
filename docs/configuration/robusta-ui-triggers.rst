Robusta UI Triggers
############################

Robusta's UI can pull limited data from your clusters, like a list of running pods.

Minimum Requirements
-------------------------

Both Robusta's Helm chart and CLI versions must be at least :code:`0.9.11`.

Checking Robusta's Helm Chart Version
*********************************************

Check Robusta's version by running ``helm list --filter robusta``

To upgrade your cluster to the latest version, see :ref:`Helm Upgrade <Simple Upgrade>`.

.. warning::

    If you have multiple clusters, you must do this per cluster!

Robusta CLI
*********************************************
Check your current CLI version by running: ``robusta version``

To upgrade your CLI to latest version, run: :code:`pip install -U robusta-cli --no-cache`

Multi Cluster Support
-------------------------

To use this feature on multiple clusters, make sure all clusters with Robusta share these values:

* ``globalConfig.account_id``
* ``globalConfig.signing_key``
* ``rsa``

These values are inside Robusta's Helm values. Refer to :ref:`Installation Guide` for more details.