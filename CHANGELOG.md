# Changelog

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

**New Features**:
- None

**Bug Fixes:**
- None

**Improvements:**
- None

**Other Changes:**
- None
