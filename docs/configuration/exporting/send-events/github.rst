GitHub
=======

Forward GitHub repository events (deployments, releases, workflow runs) to Robusta as ``change`` events.

Prerequisites
-------------

* A Robusta account with API access.
* Your Robusta ``account_id``, found in ``generated_values.yaml``.
* A Robusta API key with ``Read/Write`` access to alerts.
* GitHub admin access to the repository or organization.

Webhook URL
-----------

.. code-block::

    https://api.robusta.dev/webhooks?account_id=<ACCOUNT_ID>&origin=github&type=change

Configure GitHub
----------------

1. In your repository or organization, go to **Settings → Webhooks → Add webhook**.
2. Set **Payload URL** to the URL above.
3. Set **Content type** to ``application/json``.
4. GitHub webhooks support a single ``X-Hub-Signature-256`` header but no custom ``Authorization`` header. Authenticate by appending the API key to the URL:

   .. code-block::

       https://api.robusta.dev/webhooks?account_id=<ACCOUNT_ID>&origin=github&type=change&token=<ROBUSTA_API_KEY>

   .. warning::

      Tokens embedded in URLs can leak via browser history, server access logs, proxy logs, and HTTP ``Referer`` headers. Prefer header-based authentication when the vendor supports it. When a query-string token is the only option, mitigate exposure by using a dedicated, narrowly scoped API key with the minimum required permissions, rotating it on a regular cadence, and revoking it immediately if a leak is suspected.

5. Choose the events to deliver (``Deployments``, ``Workflow runs``, ``Releases``, etc.) and save.

Verify
------

Trigger a workflow run or push a release. The event should appear in **Settings → Delivery Log** and on the Robusta timeline.
