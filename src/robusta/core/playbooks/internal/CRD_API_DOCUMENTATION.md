# Robusta CRD API Documentation

This document describes the new kubectl-based CRD API actions available in Robusta for interacting with Kubernetes Custom Resources.

## Overview

The CRD API provides five main actions for interacting with Kubernetes resources and Custom Resource Definitions (CRDs):

1. **kubectl_describe** - Get detailed description of any Kubernetes resource
2. **fetch_resource_yaml** - Get the YAML representation of a resource
3. **fetch_resource_events** - Get events related to a specific resource
4. **fetch_crds** - List all Custom Resource Definitions in the cluster
5. **fetch_cr_instances** - List all instances of a specific Custom Resource type

## Actions

### 1. kubectl_describe

Fetches a detailed description of a Kubernetes resource using `kubectl describe`.

#### Parameters (ResourceParams)
- `kind` (string, required): The resource type (e.g., "pod", "deployment", "service")
- `name` (string, required): The resource name
- `namespace` (string, optional): The namespace (omit for cluster-scoped resources)

#### Response
- Returns a **FileBlock** containing the full kubectl describe output as a text file

#### Example Usage
```yaml
action: kubectl_describe
params:
  kind: deployment
  name: nginx-deployment
  namespace: production
```

#### Example Response
```
File: production_deployment_nginx-deployment_describe.txt
---
Name:                   nginx-deployment
Namespace:              production
CreationTimestamp:      Mon, 15 Jan 2024 10:30:00 +0000
Labels:                 app=nginx
Annotations:            deployment.kubernetes.io/revision: 3
Selector:               app=nginx
Replicas:               3 desired | 3 updated | 3 total | 3 available | 0 unavailable
...
```

---

### 2. fetch_resource_yaml

Fetches the complete YAML representation of a resource using `kubectl get -o yaml`.

#### Parameters (ResourceParams)
- `kind` (string, required): The resource type
- `name` (string, required): The resource name
- `namespace` (string, optional): The namespace

#### Response
- Returns a **FileBlock** containing the complete YAML definition

#### Example Usage
```yaml
action: fetch_resource_yaml
params:
  kind: configmap
  name: app-config
  namespace: default
```

#### Example Response
```yaml
File: default_configmap_app-config.yaml
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: default
data:
  database.url: "postgres://localhost:5432/myapp"
  cache.ttl: "3600"
...
```

---

### 3. fetch_resource_events

Fetches all Kubernetes events related to a specific resource.

#### Parameters (ResourceParams)
- `kind` (string, required): The resource type (use exact kind like "Pod", "Deployment")
- `name` (string, required): The resource name
- `namespace` (string, optional): The namespace

#### Response
- Returns a **TableBlock** with columns: Type, Reason, Age, From, Message
- Or a **MarkdownBlock** if no events are found

#### Example Usage
```yaml
action: fetch_resource_events
params:
  kind: Pod
  name: nginx-pod-abc123
  namespace: production
```

#### Example Response
| Type | Reason | Age | From | Message |
|------|--------|-----|------|---------|
| Normal | Scheduled | 2024-01-15 | default-scheduler | Successfully assigned production/nginx-pod-abc123 to node-1 |
| Normal | Pulling | 2024-01-15 | kubelet (node-1) | Pulling image "nginx:latest" |
| Normal | Pulled | 2024-01-15 | kubelet (node-1) | Successfully pulled image "nginx:latest" |
| Normal | Created | 2024-01-15 | kubelet (node-1) | Created container nginx |
| Normal | Started | 2024-01-15 | kubelet (node-1) | Started container nginx |

---

### 4. fetch_crds

Lists all Custom Resource Definitions available in the cluster.

#### Parameters
- None (this action doesn't require parameters)

#### Response
- Returns a **JsonBlock** with detailed CRD information
- Also returns a **TableBlock** with summary (Kind, API Version, Scope, Plural, Created At)

#### Example Usage
```yaml
action: fetch_crds
```

#### Example Response

**JSON Block:**
```json
[
  {
    "apiVersion": "cert-manager.io/v1",
    "kind": "Certificate",
    "plural": "certificates",
    "scope": "Namespaced",
    "createdAt": "2024-03-15T10:23:45Z",
    "additionalPrinterColumns": [
      {
        "name": "READY",
        "type": "string",
        "jsonPath": ".status.conditions[?(@.type==\"Ready\")].status"
      },
      {
        "name": "SECRET",
        "type": "string",
        "jsonPath": ".spec.secretName"
      },
      {
        "name": "ISSUER",
        "type": "string",
        "jsonPath": ".spec.issuerRef.name"
      }
    ]
  },
  {
    "apiVersion": "monitoring.coreos.com/v1",
    "kind": "Prometheus",
    "plural": "prometheuses",
    "scope": "Namespaced",
    "createdAt": "2024-02-10T14:52:18Z",
    "additionalPrinterColumns": [
      {
        "name": "VERSION",
        "type": "string",
        "jsonPath": ".spec.version"
      },
      {
        "name": "REPLICAS",
        "type": "integer",
        "jsonPath": ".spec.replicas"
      }
    ]
  }
]
```

**Table Summary:**
| Kind | API Version | Scope | Plural | Created At |
|------|------------|-------|--------|------------|
| Certificate | cert-manager.io/v1 | Namespaced | certificates | 2024-03-15T10:23:45Z |
| Prometheus | monitoring.coreos.com/v1 | Namespaced | prometheuses | 2024-02-10T14:52:18Z |
| ServiceMonitor | monitoring.coreos.com/v1 | Namespaced | servicemonitors | 2024-02-10T14:53:01Z |

---

### 5. fetch_cr_instances

Lists all instances of a specific Custom Resource type.

#### Parameters (CRInstancesParams)
- `kind` (string, required): The resource type (can be singular, plural, or Kind)
- `namespace` (string, optional): The namespace (omit to search all namespaces)
- `fields` (list of strings, optional): Specific fields to extract from each instance

#### Response
- Returns a **JsonBlock** with the requested instance data

#### Field Path Syntax
Fields support dot notation for nested access. Both JSONPath style (with leading dot) and plain paths work:
- ✅ `spec.replicas`
- ✅ `.spec.replicas` (JSONPath style from CRD output)
- ✅ `status.conditions[0].type` (array access not currently supported)
- ✅ `metadata.labels.app`

#### Example Usage

##### Example 1: List all Prometheus instances
```yaml
action: fetch_cr_instances
params:
  kind: prometheuses
```

##### Example 2: List Certificates in a specific namespace
```yaml
action: fetch_cr_instances
params:
  kind: certificates
  namespace: production
```

##### Example 3: List with specific fields
```yaml
action: fetch_cr_instances
params:
  kind: prometheuses
  fields:
    - spec.version
    - spec.replicas
    - status.phase
```

##### Example 4: Using JSONPath fields from CRD output
```yaml
# First, get the CRD to see additionalPrinterColumns
action: fetch_crds

# Then use those field paths directly
action: fetch_cr_instances
params:
  kind: certificates
  fields:
    - .status.conditions[?(@.type=="Ready")].status  # Note: Complex JSONPath not fully supported
    - .spec.secretName
    - .spec.issuerRef.name
```

#### Example Response
```json
[
  {
    "name": "prometheus-main",
    "namespace": "monitoring",
    "spec.version": "v2.41.0",
    "spec.replicas": 2,
    "status.phase": "Running"
  },
  {
    "name": "prometheus-secondary",
    "namespace": "monitoring",
    "spec.version": "v2.40.0",
    "spec.replicas": 1,
    "status.phase": "Running"
  }
]
```

## Common Use Cases

### 1. Debugging a Pod Issue
```yaml
# Get pod description
action: kubectl_describe
params:
  kind: pod
  name: failing-pod
  namespace: production

# Check recent events
action: fetch_resource_events
params:
  kind: Pod
  name: failing-pod
  namespace: production

# Get full YAML for detailed inspection
action: fetch_resource_yaml
params:
  kind: pod
  name: failing-pod
  namespace: production
```

### 2. Exploring Custom Resources
```yaml
# First, discover what CRDs are available
action: fetch_crds

# Then list instances of a specific type
action: fetch_cr_instances
params:
  kind: certificates
  namespace: production

# Get details on a specific instance
action: kubectl_describe
params:
  kind: certificate
  name: api-tls-cert
  namespace: production
```

### 3. Monitoring Operator-Managed Resources
```yaml
# List all Prometheus instances with key fields
action: fetch_cr_instances
params:
  kind: prometheuses
  fields:
    - spec.version
    - spec.replicas
    - spec.retention
    - status.availableReplicas
```

## Important Notes

1. **Authentication**: These actions use kubectl, so they inherit the permissions of the service account running Robusta.

2. **Resource Names**:
   - For `kubectl_describe` and `fetch_resource_yaml`, use lowercase singular names (e.g., "pod", "deployment")
   - For `fetch_resource_events`, use the exact Kind with proper capitalization (e.g., "Pod", "Deployment")
   - For `fetch_cr_instances`, any form works (singular, plural, or Kind)

3. **Namespace Handling**:
   - Always specify namespace for namespaced resources
   - Omit namespace for cluster-scoped resources (e.g., nodes, clusterroles)
   - For `fetch_cr_instances`, omitting namespace searches all namespaces

4. **Field Extraction**:
   - Simple nested paths are supported (e.g., `spec.replicas`)
   - Leading dots from JSONPath are automatically handled
   - Complex JSONPath expressions (filters, wildcards) are not currently supported

5. **Performance**:
   - These actions execute kubectl commands, which may be slower than direct API calls
   - Consider caching or rate limiting for high-frequency operations

6. **Error Handling**:
   - Actions will raise `ActionException` if kubectl commands fail
   - Check that resources exist and you have proper permissions

## Integration Example

Here's how you might use these actions in a Robusta playbook:

```yaml
customPlaybooks:
- triggers:
  - on_prometheus_alert:
      alert_name: CertificateExpiringSoon
  actions:
  - fetch_resource_events:
      params:
        kind: Certificate
        name: "{{ alert.labels.certificate_name }}"
        namespace: "{{ alert.labels.namespace }}"
  - kubectl_describe:
      params:
        kind: certificate
        name: "{{ alert.labels.certificate_name }}"
        namespace: "{{ alert.labels.namespace }}"
```

## Troubleshooting

### Common Issues

1. **"kubectl command failed" errors**
   - Ensure kubectl is available in the runner container
   - Check RBAC permissions for the service account
   - Verify the resource exists

2. **Empty results from fetch_cr_instances**
   - Check the CRD is installed (`fetch_crds`)
   - Verify the resource type spelling
   - Ensure you have permission to list the resource

3. **Field extraction returning null**
   - Verify the field path is correct
   - Check if the field exists on all instances
   - Remember that array access in field paths is limited

4. **No events found**
   - Events may have expired (default TTL is 1 hour)
   - Ensure you're using the correct Kind (capitalized)
   - Check the resource name and namespace match exactly

## Version Requirements

- Robusta runner with kubectl binary installed
- Kubernetes cluster access via kubeconfig or service account
- Appropriate RBAC permissions for the resources you want to access

## Support

For issues or questions about these CRD API actions, please:
1. Check the Robusta logs for detailed error messages
2. Verify kubectl works manually in the runner pod
3. Open an issue in the Robusta GitHub repository with details