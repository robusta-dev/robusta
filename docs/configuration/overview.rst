:hide-toc:
Common Settings
==========================

Robusta is configured using Helm values. Here are common settings you might want to change:

* Sinks - where should Robusta send notifications? Slack, MSTeams, Telegram, Discord, and more

All Settings
=============
All possible values for Robusta can be listed like so:

.. code-block:: yaml

    helm repo add robusta https://robusta-charts.storage.googleapis.com && helm repo update
    helm show values robusta/robusta

.. admonition:: Do not use the values.yaml file on GitHub
    :class: warning

    It's tempting to look at ``helm/robusta/values.yaml`` in our GitHub repo for reference.
    This is the wrong file to use, as it has empty placeholders that are filled in for releases.

Most used settings
^^^^^^^^^^^^^^^^^^

.. grid:: 1 1 2 3
    :gutter: 3

    .. grid-item-card:: :octicon:`book;1em;` Global config
        :class-card: sd-bg-light sd-bg-text-light
        :link: global-config
        :link-type: doc

        Define reusable parameters for all playbooks
        
    .. grid-item-card:: :octicon:`book;1em;` Loading additional playbooks
        :class-card: sd-bg-light sd-bg-text-light
        :link: additional-playbooks
        :link-type: doc

        Import playbooks from GIT sources using HTTPS or SSH
   
    .. grid-item-card:: :octicon:`book;1em;` Sending alerts to Robusta
        :class-card: sd-bg-light sd-bg-text-light
        :link: alert-manager
        :link-type: doc

        Use non Robusta embeded prometheus
