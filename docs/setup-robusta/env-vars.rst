.. _Robusta env var reference:

Environment Variable Reference
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This page lists the environment variables most commonly set when deploying Robusta. It's intended as a
quick lookup so you don't have to read the source code to understand what each variable does or which
component reads it.

These variables are set in your Helm values file:

* On the runner, via ``runner.additional_env_vars``
* On HolmesGPT (when installed via the Robusta Helm chart with ``enableHolmesGPT: true``), via ``holmes.additionalEnvVars``

Both fields accept the standard Kubernetes env var format, so values can be hardcoded or pulled from
``secretKeyRef`` / ``configMapKeyRef``. See :ref:`Managing Secrets` for examples.

.. note::

    The lists below cover variables a Robusta user typically needs to set. The runner and Holmes both
    read additional internal/tuning variables that are not listed here. If a variable you need isn't
    listed, check ``src/robusta/core/model/env_vars.py`` (runner) or ``holmes/common/env_vars.py``
    (Holmes) in the respective repositories.

Runner (``runner.additional_env_vars``)
---------------------------------------------

Connecting to the Robusta backend
==========================================

.. list-table::
   :widths: 25 50 25
   :header-rows: 1

   * - Variable
     - Purpose
     - Default
   * - ``ROBUSTA_API_ENDPOINT``
     - Robusta SaaS API endpoint. Override for non-default regions (e.g. EU).
     - ``https://api.robusta.dev``
   * - ``ROBUSTA_UI_DOMAIN``
     - Robusta UI domain used to build links in notifications.
     - ``https://platform.robusta.dev``
   * - ``ROBUSTA_TELEMETRY_ENDPOINT``
     - Endpoint that receives telemetry pings.
     - ``https://api.robusta.dev/telemetry``
   * - ``RELAY_EXTERNAL_ACTIONS_URL``
     - Endpoint that the runner posts external action requests to.
     - ``https://api.robusta.dev/integrations/generic/actions``
   * - ``WEBSOCKET_RELAY_ADDRESS``
     - WebSocket relay address used for action callbacks from the UI.
     - ``wss://relay.robusta.dev``
   * - ``ENABLE_TELEMETRY``
     - Set to ``false`` to disable telemetry.
     - ``true``

Credentials (typically referenced from secrets)
=====================================================

These are usually defined as env vars on the runner pod and then referenced from ``globalConfig`` /
``sinksConfig`` using the ``{{ env.X }}`` syntax. See
:ref:`Loading Robusta credentials from secrets` for the full pattern.

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - Variable
     - Purpose
   * - ``ACCOUNT_ID``
     - Convention for an env var that holds your Robusta account ID. Referenced from ``globalConfig.account_id`` as ``{{ env.ACCOUNT_ID }}``.
   * - ``SIGNING_KEY``
     - Convention for an env var that holds your runner signing key. Referenced from ``globalConfig.signing_key`` as ``{{ env.SIGNING_KEY }}``.
   * - ``ROBUSTA_UI_TOKEN``
     - Convention for an env var that holds the Robusta UI sink token. Referenced from ``sinksConfig[].robusta_sink.token`` as ``{{ env.ROBUSTA_UI_TOKEN }}``. The same env var should also be set on Holmes (see below).

.. note::

    The names ``ACCOUNT_ID``, ``SIGNING_KEY``, and ``ROBUSTA_UI_TOKEN`` are conventions — you can pick
    any env var names you like, as long as the names you set on the pod match the names you reference
    from ``globalConfig`` / ``sinksConfig``.

Other commonly set runner variables
=========================================

.. list-table::
   :widths: 25 50 25
   :header-rows: 1

   * - Variable
     - Purpose
     - Default
   * - ``HTTP_PROXY`` / ``HTTPS_PROXY``
     - Forward outbound traffic through an HTTP proxy. See :ref:`Deploying Behind Proxies`.
     - unset
   * - ``CERTIFICATE``
     - Additional CA certificate (base64-encoded). Useful for self-signed corporate proxies.
     - unset
   * - ``IS_OPENSHIFT``
     - Set to ``true`` when running on OpenShift. See :ref:`OpenShift`.
     - ``false``
   * - ``CLUSTER_DOMAIN``
     - Override the cluster's DNS domain.
     - ``cluster.local``

HolmesGPT (``holmes.additionalEnvVars``)
-----------------------------------------------

Variables read by HolmesGPT when installed via the Robusta Helm chart (``enableHolmesGPT: true``).

Connecting to the Robusta backend
==========================================

.. list-table::
   :widths: 25 50 25
   :header-rows: 1

   * - Variable
     - Purpose
     - Default
   * - ``ROBUSTA_AI``
     - Set to ``"true"`` to enable the Robusta-hosted AI integration. Required for users who want Holmes to talk to the Robusta backend.
     - unset
   * - ``ROBUSTA_UI_TOKEN``
     - Robusta UI sink token. Required for Holmes to authenticate to the Robusta backend; should be set to the same token as the runner's ``robusta_sink``.
     - unset
   * - ``ROBUSTA_ACCOUNT_ID``
     - Your Robusta account ID. Usually derived from ``ROBUSTA_UI_TOKEN`` automatically; only set explicitly if instructed by support.
     - unset
   * - ``ROBUSTA_API_ENDPOINT``
     - Robusta SaaS API endpoint. Override for non-default regions.
     - ``https://api.robusta.dev``
   * - ``ROBUSTA_UI_DOMAIN``
     - Robusta UI domain.
     - ``https://platform.robusta.dev``

LLM and runtime
========================

.. list-table::
   :widths: 25 50 25
   :header-rows: 1

   * - Variable
     - Purpose
     - Default
   * - ``MODEL``
     - LLM model identifier when using a single-model setup (e.g. ``gpt-4o``). For multi-model setups, configure ``modelList`` in Helm instead.
     - unset
   * - ``OPENAI_API_KEY`` / ``AZURE_OPENAI_ENDPOINT`` / ``ANTHROPIC_API_KEY`` / etc.
     - LLM provider credentials. Set the ones your model requires.
     - unset
   * - ``LOG_LEVEL``
     - Log verbosity (``DEBUG``, ``INFO``, ``WARNING``, ``ERROR``).
     - ``INFO``
   * - ``HTTP_PROXY`` / ``HTTPS_PROXY``
     - Forward outbound traffic through an HTTP proxy.
     - unset
   * - ``CERTIFICATE``
     - Additional CA certificate (base64-encoded).
     - unset
   * - ``ENABLE_TELEMETRY``
     - Set to ``false`` to disable telemetry.
     - ``false``

Quick reference: which component needs which credential?
-----------------------------------------------------------------

.. list-table::
   :widths: 35 25 25 15
   :header-rows: 1

   * - Setting
     - Runner
     - Holmes
     - Set in
   * - ``account_id``
     - ✅
     - —
     - ``globalConfig``
   * - ``signing_key``
     - ✅
     - —
     - ``globalConfig``
   * - Robusta UI / sink token
     - ✅
     - ✅
     - ``sinksConfig`` (runner) + ``additionalEnvVars`` (Holmes)
   * - ``ROBUSTA_API_ENDPOINT`` (non-default region)
     - ✅
     - ✅
     - ``additional_env_vars`` / ``additionalEnvVars``
   * - ``ROBUSTA_UI_DOMAIN`` (non-default region)
     - ✅
     - ✅
     - ``additional_env_vars`` / ``additionalEnvVars``
   * - ``ROBUSTA_AI=true``
     - —
     - ✅
     - ``additionalEnvVars``

See also
-----------

* :ref:`Managing Secrets` — how to keep these values out of plain text Helm values
* :ref:`Deploying Behind Proxies` — proxy-related env vars
* `Runner env vars in source <https://github.com/robusta-dev/robusta/blob/master/src/robusta/core/model/env_vars.py>`_
* `HolmesGPT env vars in source <https://github.com/robusta-dev/holmesgpt/blob/master/holmes/common/env_vars.py>`_
