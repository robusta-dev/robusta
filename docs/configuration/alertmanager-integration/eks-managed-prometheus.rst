AWS Managed Prometheus Alerts
******************************

AWS Managed Prometheus uses Amazon Managed Grafana for alerting. To send alerts to Robusta, configure your Grafana instance to forward alerts.

For configuring metric querying from AWS Managed Prometheus, see :doc:`/configuration/metric-providers-aws`.

Send Alerts to Robusta
======================

Since AWS Managed Prometheus doesn't have a built-in AlertManager, you'll need to:

1. Set up Amazon Managed Grafana with your AMP workspace
2. Configure Grafana alerts to send to Robusta
3. See :doc:`grafana-alert-manager` for detailed Grafana alerting setup

Configure Metric Querying
=========================

To enable Robusta to pull metrics from AWS Managed Prometheus, see :doc:`/configuration/metric-providers-aws`.
