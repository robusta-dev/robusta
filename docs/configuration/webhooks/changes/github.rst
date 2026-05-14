GitHub
=======

Forward GitHub events (pushes, pull requests, releases, deployments) to
Robusta so HolmesGPT can correlate code changes with alert spikes.

Prerequisites
-------------

* A Robusta account with API access.
* Your Robusta ``account_id``, found in ``generated_values.yaml``.
* A Robusta API key with ``Read/Write`` access to alerts.
* Repository admin access on the GitHub repository you want to track.

Webhook URL
-----------

.. code-block::

    https://api.robusta.dev/webhooks?type=change&origin=github&account_id=<ACCOUNT_ID>

Configure GitHub
----------------

In your GitHub repository:

1. Open **Settings → Webhooks → Add webhook**.
2. **Payload URL**: paste the webhook URL above.
3. **Content type**: ``application/json``.
4. **Secret**: leave empty — Robusta authenticates by API key, not by HMAC.
5. **SSL verification**: keep enabled.
6. Under **Which events would you like to trigger this webhook?**,
   select **Let me select individual events** and tick:

   * **Pushes** (commits to any branch)
   * **Pull requests** (open/close/merge)
   * **Releases**
   * **Deployments** (optional, if you use GitHub Deployments)
7. **Active**: checked. **Save**.

GitHub does not support custom request headers on webhooks. Pass the
Robusta API key on the URL instead:

.. code-block::

    https://api.robusta.dev/webhooks?type=change&origin=github&account_id=<ACCOUNT_ID>&token=<ROBUSTA_API_KEY>

Example Payload (push)
----------------------

.. code-block:: json

    {
      "ref": "refs/heads/main",
      "before": "abc...",
      "after": "def...",
      "repository": { "full_name": "acme/checkout" },
      "sender": { "login": "jane" },
      "commits": [
        { "id": "abcdef1", "message": "fix checkout race" }
      ],
      "compare": "https://github.com/acme/checkout/compare/abc...def"
    }

Supported Events
----------------

The parser recognizes the four most common event shapes:

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - Event
     - What lands on the timeline
   * - ``push``
     - ``GitHub push: <repo>@<branch>``; commits listed in description.
   * - ``pull_request``
     - ``GitHub PR #<n> <action>: <title>``; base / head SHAs in diff.
   * - ``release``
     - ``GitHub release <name> (<action>)``; release notes in description.
   * - ``deployment``
     - ``GitHub deployment to <env>: <repo>@<ref>``.

Other event types fall through to the generic change parser — they're
still stored and visible in the Delivery Log, just without a per-event
mapping.

Test the Integration
--------------------

Push a commit (or create a draft release) on the configured repository.
The event should appear on the Robusta timeline within a few seconds.
