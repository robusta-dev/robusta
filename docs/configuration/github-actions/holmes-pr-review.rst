HolmesGPT PR Review
===================

.. note::
    This integration is available with the Robusta SaaS platform and self-hosted commercial plans. It is not available in the open-source version.

Use HolmesGPT as a GitHub Action to automatically review pull requests. On every PR open, reopen, or push, the action asks HolmesGPT to review the change and post its review as a comment on the pull request. You control what Holmes checks by editing the prompt — it can flag risky changes, check code against runbooks, cross-reference logs or metrics, or run any investigation available via its :doc:`data sources <../holmesgpt/main-features>`.

Example review posted by HolmesGPT on a pull request:

.. image:: /images/holmes-pr-review-example.png
  :width: 700
  :align: center

How It Works
------------

1. A pull request event triggers the GitHub Action.
2. The action calls the :ref:`Holmes Chat API <holmes-chat-api>` with your review prompt and the PR URL.
3. HolmesGPT uses the GitHub toolset to read the pull request, reason about it using the data sources you have configured, and post its review as a comment on the PR.

Prerequisites
-------------

Before setting up the action, you must enable the Holmes GitHub integration so HolmesGPT can read pull requests and post comments. Follow the `HolmesGPT GitHub toolset guide <https://holmesgpt.dev/latest/data-sources/builtin-toolsets/github-mcp/>`_.

Setup
-----

Step 1: Create a Robusta API Key
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In the Robusta Platform, navigate to **Settings** → **API Keys** and click **New API Key**.

Give the key a descriptive name (for example, ``HolmesGPT github action``) and check the **Robusta AI Write** capability. Click **Generate API Key** and copy the key — you will not be able to view it again.

.. image:: /images/new-api-key.png
  :width: 600
  :align: center

Step 2: Get Your Account ID and Cluster ID
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In the Robusta Platform, navigate to **Settings** → **Workspace** and copy your **Account ID**.

Then pick the cluster HolmesGPT should run the investigation on and copy its **Cluster ID**. Any cluster connected to your account can be used — HolmesGPT will use its data sources (logs, metrics, Kubernetes state, etc.) from that cluster when reviewing the PR.

Step 3: Add GitHub Secrets
^^^^^^^^^^^^^^^^^^^^^^^^^^

In your GitHub repository, go to **Settings** → **Secrets and variables** → **Actions** and add the following repository secrets:

.. list-table::
   :widths: 25 75
   :header-rows: 1
   :width: 100%

   * - Secret
     - Value
   * - ``ROBUSTA_API_KEY``
     - The API key you generated in Step 1.
   * - ``ROBUSTA_ACCOUNT_ID``
     - The account ID from Step 2.
   * - ``ROBUSTA_CLUSTER_ID``
     - The cluster ID from Step 2.

Step 4: Add the Workflow File
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Create a new file in your repository at ``.github/workflows/holmes-pr-review.yaml`` with the following contents:

.. code-block:: yaml

    name: Holmes PR review
    on:
      pull_request:
        types: [opened, synchronize, reopened]
    jobs:
      review:
        runs-on: ubuntu-latest
        env:
          RELAY_BASE_URL: https://api.robusta.dev
          ACCOUNT_ID: ${{ secrets.ROBUSTA_ACCOUNT_ID }}
          API_KEY: ${{ secrets.ROBUSTA_API_KEY }}
          CLUSTER_ID: ${{ secrets.ROBUSTA_CLUSTER_ID }}
          PR_URL: ${{ github.event.pull_request.html_url }}
          PROMPT: |
            Review the pull request at the URL below. Flag risky, unclear, or
            incomplete changes. You MUST post your review as a single PR comment
            on that pull request using your GitHub toolset. Do not reply with the
            review in chat only — posting the comment is required.
        steps:
          - name: Ask Holmes (Holmes posts the comment)
            run: |
              set -euo pipefail
              jq -n \
                --arg ask "$PROMPT"$'\n\nPull request: '"$PR_URL" \
                --arg cluster "$CLUSTER_ID" \
                '{ask: $ask, cluster_id: $cluster, stream: false}' > body.json
              curl -fsS --retry 2 \
                -H "Authorization: Bearer $API_KEY" \
                -H "Content-Type: application/json" \
                --data-binary @body.json \
                "$RELAY_BASE_URL/api/holmes/$ACCOUNT_ID/chat" > response.json
              # Log analysis for debugging; Holmes is expected to have posted the comment.
              jq -r '.analysis // "(no analysis text returned)"' response.json

Commit and push the workflow file. The next pull request opened against the repository will trigger the action, and HolmesGPT will post its review as a PR comment.

Customizing the Review Prompt
-----------------------------

The ``PROMPT`` environment variable controls what HolmesGPT checks. Edit it to match your team's review policy. For example:

* Enforce coding standards or architecture rules.
* Cross-reference the change against runbooks, incident history, or documentation in Confluence/Notion.
* Validate that related Kubernetes manifests, Helm values, or Prometheus alert rules are consistent with the code changes.
* Require that PRs changing specific paths include tests.

Whatever you put in the prompt, keep the instruction to post the review as a PR comment — otherwise Holmes will return the review only in the API response.

Configuration Reference
-----------------------

The action calls the :ref:`Holmes Chat API <holmes-chat-api>`. Any parameter supported by that endpoint (for example, ``model`` or ``additional_system_prompt``) can be added to the JSON body in the workflow.

Troubleshooting
---------------

No comment appears on the PR
    Check the action logs. The final step prints the ``analysis`` field returned by the API — if it contains a review but no comment was posted, the GitHub integration is not enabled for HolmesGPT. Re-check the `GitHub toolset guide <https://holmesgpt.dev/latest/data-sources/builtin-toolsets/github-mcp/>`_.

``401 Unauthorized``
    The ``ROBUSTA_API_KEY`` secret is missing, invalid, or lacks the **Robusta AI Write** capability. Regenerate the key in the Robusta Platform.

``404 Not Found`` or cluster errors
    The ``ROBUSTA_CLUSTER_ID`` secret does not match a cluster connected to your account. Copy the cluster ID from the Robusta Platform again.
