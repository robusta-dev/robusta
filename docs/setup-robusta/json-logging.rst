JSON Log Format
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

By default, Robusta components emit human-readable, colored text logs. You can
switch them to **structured JSON logs** (one JSON object per line), which are
easier to index, search, and filter with log collectors such as Filebeat,
Fluent Bit, or Loki.

Enabling JSON Logs
-------------------------------------

Set the ``global.enableJsonLogsFormat`` value in your Helm values:

.. code-block:: yaml

    global:
      enableJsonLogsFormat: true

This single switch is shared across the Robusta components:

* **robusta-runner** emits JSON logs.
* **KRR** scan jobs inherit the setting from the runner (when scan results are
  pushed back over the API, which is the default).
* **HolmesGPT** (when deployed via the chart) emits JSON logs as well — the
  ``global`` value is passed through to the Holmes sub-chart.

The default is ``false``, which preserves the existing colored text output. No
change is needed unless you want JSON logs.

Log Format
-------------------------------------

When enabled, each log line is a JSON object. The ``level`` field is emitted as
``severity`` (matching the Google Cloud Logging convention used across Robusta
services):

.. code-block:: json

    {"asctime": "2026-07-14T11:54:51", "severity": "INFO", "name": "robusta", "message": "..."}

KRR Enforcer
-------------------------------------

The KRR Enforcer is installed from its own chart (``krr-enforcer``) rather than
as part of the Robusta chart, so it exposes its own value:

.. code-block:: yaml

    enableJsonLogsFormat: true

If it is deployed under an umbrella chart that sets ``global.enableJsonLogsFormat``,
that value is honored as a fallback.
