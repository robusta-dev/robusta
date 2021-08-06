# Changelog

## v0.4.51
**New Features**:
- Sinks - **Breaking Changes**: From now on, no need to explicitly publish playbook results to a specific target. 
  
  Within the playbook's code we only need to create a ``Finding`` object. It will be published to the configured ``sinks``
  
  For example:
  instead of writing: 
  
  ``send_to_slack(...)``
  
  write: 
  
  ``event.finding = Finding(title="...")``
  
- Slack api key: Slack api key was moved from the ``runner`` deployment file, into the slack sink configuration in the ``active_playbooks.yaml`` configuration file.

## v0.4.50
**New Features**:
- New enrichers: NodeBashEnricher, CPUThrottlingAnalysis, and DeploymentStatusEnricher
- Add a log line when an alert is silenced. The format is `Silencing alert {alert_name} due to silencer {silencer_name}`

**Bug Fixes**:
- Fix handling of Slack messages with very long titles or contents. This bug caused certain alerts to be dropped and not forwarded to Slack.

**Other Changes**:
- Minor formatting and styling changes to Slack messages
- Documentation improvements

## v0.4.46
**Breaking Changes:**
- The json format for deployment_babysitter events sent to Kafka was updated.

**New Features**:
- New `pod_babysitter` which is similar to the `deployment_babysitter` but tracks pods.

## v0.4.45
**Upgrade Steps:**
- If you use the `alerts_integration` playbook and set an override for the default_enricher:
  - Update the `default_enricher` field from `default_enricher: your_enricher` to:
    
```yaml
default_enrichers:
  - name: "your_enricher"`
```

**Breaking Changes:**
- The `default_enricher` field for the `alerts_integration` playbook was changed from a string to an array.
