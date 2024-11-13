Troubleshooting runbook: HighCheckoutErrorRate
##################################################

This alert fires when the error rate on checkout requests is high

Troubleshooting steps
----------------------

1. Check the account-service workload logs for errors
2. Verify that the nginx-deployment is working properly
3. Check that the redis workload is working properly

If any of the above has error, this is most likely the issue
