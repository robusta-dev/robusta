Upgrade Guide
##################

Robusta is installed with Helm, so Robusta upgrades are just Helm upgrades.

Helm Upgrade
------------------------------

This will upgrade Robusta while preserving any custom settings:

.. code-block:: bash

    helm repo update
    helm upgrade robusta robusta/robusta --values=values.yaml

We recommend running the above command exactly as written.

.. admonition:: Where is my values.yaml?

    If you have lost your ``values.yaml`` file, you can extract it from the cluster:

    .. code-block:: bash

         helm get values robusta

Notes
^^^^^^^^^^^^^^^^^^^^^^^^
1. We do **not** recommend running ``helm upgrade --reuse-values`` `as it doesn't update default values changed in the chart.
<https://medium.com/@kcatstack/understand-helm-upgrade-flags-reset-values-reuse-values-6e58ac8f127e>`_

2. To install a Robusta pre-release, run ``helm upgrade`` with the ``--devel`` flag.