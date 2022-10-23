Overview
==========================

Robusta is configured using Helm values. This page documents the important values.

All possible values can be found by running:

.. code-block:: yaml

    helm repo add robusta https://robusta-charts.storage.googleapis.com && helm repo update
    helm show values robusta/robusta

Do not use ``helm/robusta/values.yaml`` in the GitHub repo. It has some empty placeholders which are replaced during
our release process.


