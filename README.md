# About Robusta
Robusta is an open source platform for automated troubleshooting and maintenance. We turn Kubernetes expertise into re-usable code.

Robusta automates everything that happens after you deploy your application.

You can use any of our builtin actions, or easily add your own.

## Examples
You can monitor crashing pods and send their logs to Slack:

```yaml
triggers:
  - on_prometheus_alert:
      alert_name: KubePodCrashLooping
actions:
  - logs_enricher: {}
sinks:
  - slack
```

There are also builtin automations to analyze common alerts.

You can also trigger automations manually. For example, [attach a debugger to a python pod](https://docs.robusta.dev/master/catalog/actions/python-troubleshooting.html#python-debugger):
```commandline
robusta playbooks trigger python_debugger name=mypod namespace=default
```

[There are over 50 builtin automations.](https://docs.robusta.dev/master/catalog/actions/index.html)

# Installing Robusta

1. Install our python cli:

```commandline
python3 -m pip install -U robusta-cli --no-cache
```

2. Generate a values file for Helm:
```commandline
robusta gen-config
```

3. Install Robusta with Helm:
```commandline
helm repo add robusta https://robusta-charts.storage.googleapis.com && helm repo update
helm install robusta robusta/robusta -f ./generated_values.yaml
```

Full instructions are in our [installation guide](https://docs.robusta.dev/master/getting-started/installation.html).

# Documentation
Interested? Read the [full documentation](https://docs.robusta.dev/master/index.html)
