Robusta UI Triggers
############################

| Robusta UI can pull data directly from your clusters.
| This can make investigation & troubleshooting so much easier compared to working with :code:`kube-ctl`.

Security
********
| To enjoy Robusta UI Triggers without compromising your cluster's security, we've implemented a Multi Part Authentication (MPA).
.. note::
    By default, Robusta UI will not be able to pull data from your clusters.
    This will only be available after you enable Multi Part Authentication.

Our MPA guarantees that the only way Robusta UI can pull data is if:
    1. A user is currently logged in.
    2. The UI is using a secret key that belongs to the logged in user (see Secret Key part below to understand how to get it).

The Secret Key
==============
| When MPA is enabled, Robusta creates a secret key and splits it to 2 (hence multi part).
|
| The 1st part of this key is given to you, and no one else knows about it, not even Robusta.
| The 2nd part is safely stored within Robusta.
|

The 2 parts of the secret must be used together, otherwise they won't work.
This means, for example, that even if Robusta is hacked, the attacker won't be able do anything with your clusters.

-----------

If you have any questions regarding security, don't hesitate to send us an email to support@robusa.dev and we'll be happy to answer!

Multi Cluster Support
*********************
To use this feature on multiple clusters, make sure you install Robusta with these same values across all your clusters:
    - :code:`globalConfig.account_id`
    - :code:`globalConfig.signing_key`
    - :code:`rsa`
| These values inside the :code:`values.yaml` file you use, when you run :code:`helm install robusta...`
| See `Installation Guide <https://docs.robusta.dev/master/installation.html>`_ for more details.

Minimum Requirements
********************
Robusta & Robusta CLI versions must be at least :code:`0.9.11`.

- Robusta
    - To check your current cluster version, run: :code:`helm list --filter robusta`
    - To upgrade your cluster to the latest version, run: :code:`robusta upgrade`
    - Note! You need to do this per cluster.
- Robusta CLI
    - To check your current CLI version, run: :code:`robusta version`
    - To upgrade your CLI to latest version, run: :code:`pip install -U robusta-cli --no-cache`