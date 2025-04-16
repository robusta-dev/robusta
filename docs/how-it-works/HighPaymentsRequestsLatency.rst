Troubleshooting runbook: HighPaymentsRequestsLatency
##################################################

This alert fires when there's a high latency on the payment request microservice

Troubleshooting steps
----------------------

1. Check the pods the alert is fired on for errors
2. Check that the **postgres** pod on the cluster is up and running properly. It's used to store and get payment requests.
   If the *postgres* db is unhealthy, this is probably the cause for it. For this, contact the DB INFRA team
3. Check **account-config** workload. It's also used on the payment requests flow. For errors in this workload, contact the `config management` application team

If any of the above has error, this is most likely the issue
