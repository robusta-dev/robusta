AWS CloudWatch
===============

Forward CloudWatch alarms to Robusta. CloudWatch cannot POST to arbitrary HTTPS endpoints directly, so the recipe is **CloudWatch → SNS → Lambda → Robusta**.

Prerequisites
-------------

* A Robusta account with API access.
* Your Robusta ``account_id``, found in ``generated_values.yaml``.
* A Robusta API key with ``Read/Write`` access to alerts.
* AWS account permissions to create Lambda functions and SNS topics.

Webhook URL
-----------

.. robusta-code::

    https://api.robusta.dev/webhooks?type=alert&origin=awscloudwatch&account_id=<ACCOUNT_ID>

Recipe
------

1. Create an SNS topic named ``robusta``. Add it as a notification action on the CloudWatch alarms you want forwarded.
2. Create a Lambda function (Python 3.12) and subscribe it to the ``robusta`` SNS topic. Store the Robusta API key in **Lambda → Configuration → Environment variables** as ``ROBUSTA_API_KEY``.
3. Use the following handler:

   .. robusta-code:: python

       import json
       import os
       import urllib.error
       import urllib.request

       URL = "https://api.robusta.dev/webhooks?type=alert&origin=awscloudwatch&account_id=<ACCOUNT_ID>"
       TIMEOUT_SECONDS = 5

       def lambda_handler(event, context):
           for record in event["Records"]:
               body = record["Sns"]["Message"]
               req = urllib.request.Request(
                   URL,
                   data=body.encode("utf-8"),
                   method="POST",
                   headers={
                       "Content-Type": "application/json",
                       "Authorization": f"Bearer {os.environ['ROBUSTA_API_KEY']}",
                   },
               )
               try:
                   urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS).read()
               except urllib.error.URLError as exc:
                   print(f"failed to forward CloudWatch alarm to Robusta: {exc}")
                   raise
           return {"ok": True}

4. Replace ``<ACCOUNT_ID>`` with your Robusta account ID and deploy.

Alternatively, if you already use **Amazon EventBridge → API destination**, point the destination at the same URL with a Bearer token connection — no Lambda required.

Verify
------

Use the **Test alarm** action in CloudWatch. The event should appear in **Settings → Delivery Log** and on the Robusta timeline.
