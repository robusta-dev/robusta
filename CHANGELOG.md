# Changelog

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
