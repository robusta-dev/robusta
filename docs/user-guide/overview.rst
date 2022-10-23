:hide-toc:
Overview
==========================

Robusta is configured using Helm values. This section documents all the important values. 
All possible values can be found by running:

.. code-block:: yaml

    helm repo add robusta https://robusta-charts.storage.googleapis.com && helm repo update
    helm show values robusta/robusta

.. admonition:: values.yaml on GitHub
    :class: warning

    Do not use ``helm/robusta/values.yaml`` in the GitHub repo. It has some empty placeholders which are replaced during
    our release process.

Most used settings
^^^^^^^^^^^^^^^^^^

.. grid:: 1 1 2 3
    :gutter: 3

    .. grid-item-card:: :octicon:`book;1em;` Global config
        :class-card: sd-bg-light sd-bg-text-light
        :link: global-config
        :link-type: doc

        
    .. grid-item-card:: :octicon:`book;1em;` Loading additional playbooks
        :class-card: sd-bg-light sd-bg-text-light
        :link: additional-playbooks
        :link-type: doc

   
    .. grid-item-card:: :octicon:`book;1em;` Sending alerts to Robusta
        :class-card: sd-bg-light sd-bg-text-light
        :link: alert-manager
        :link-type: doc
