Send Changes API
=================

Forward configuration, feature-flag, and deployment changes to Robusta
via the webhook endpoint. Change events surface alongside alerts on the
issue timeline so HolmesGPT can correlate "what changed" with "what
broke".

Endpoint
--------

.. code-block::

    POST https://api.robusta.dev/webhooks?type=change&origin=<ORIGIN>&account_id=<ACCOUNT_ID>

See :doc:`send-events-api` for query parameters, authentication, and
error codes.

.. toctree::
   :maxdepth: 1
   :hidden:

   changes/launchdarkly
   changes/argocd
   changes/github

Feature Flags
~~~~~~~~~~~~~

.. grid:: 1 1 2 3
    :gutter: 3

    .. grid-item-card:: :octicon:`toggle-switch;1em;` LaunchDarkly
        :class-card: sd-bg-light sd-bg-text-light
        :link: changes/launchdarkly
        :link-type: doc

GitOps & Deployments
~~~~~~~~~~~~~~~~~~~~

.. grid:: 1 1 2 3
    :gutter: 3

    .. grid-item-card:: :octicon:`rocket;1em;` Argo CD
        :class-card: sd-bg-light sd-bg-text-light
        :link: changes/argocd
        :link-type: doc

    .. grid-item-card:: :octicon:`mark-github;1em;` GitHub
        :class-card: sd-bg-light sd-bg-text-light
        :link: changes/github
        :link-type: doc
