# Patching CVEs in Robusta: Automated Workflow

This skill automates the process of identifying and patching CVE vulnerabilities in the Robusta Docker image and Python dependencies, focusing on critical, high, and medium severity issues.

## Overview

The workflow follows this systematic process:

1. **Vulnerability Scanning** - Identify all CVEs in dependencies and Docker image
2. **Severity Filtering** - Focus on critical, high, and medium severity issues
3. **Root Cause Analysis** - Determine which packages/dependencies introduce vulnerabilities
4. **Upstream Research** - Check if newer releases already include fixes
5. **Patch Implementation** - Apply fixes via dependency upgrades or Dockerfile changes
6. **Validation** - Verify CVE fixes and ensure application functionality

## Step-by-Step Process

### 1. Vulnerability Scanning

Use multiple scanning tools to identify vulnerabilities:

```bash
# Scan Docker image for vulnerabilities
docker build -t robusta:latest .
docker scout cves robusta:latest

# Scan Python dependencies for vulnerabilities
pip-audit
safety check

# Validate pyproject.toml metadata and lockfile consistency (does not perform vulnerability scanning)
poetry check
# For CVE scanning of Python dependencies, use pip-audit, safety, or poetry-audit-plugin
```

**What to extract:**
- Affected package name and version
- CVE ID and severity level
- Fixed version (if available)
- Affected version range

### 2. Severity Filtering

Process vulnerabilities in this order:
1. **Critical** - Must be fixed before release
2. **High** - Should be fixed before release
3. **Medium** - Fix when safe and non-breaking

Create a prioritized list and document each CVE:

```
CVE-XXXX-XXXXX (Critical): Package X - affects >=1.0.0,<1.2.0
  Fixed in: 1.2.5
  Status: Needs patching

CVE-YYYY-YYYYY (High): Package Y - affects >=2.0.0,<2.1.0
  Fixed in: 2.1.3
  Status: Needs patching
```

### 3. Python Dependency Patches

Two main strategies:

**Strategy A: Direct Upgrade (Preferred)**
- Check `poetry.lock` for affected packages
- Update `pyproject.toml` with patched version
- Run `poetry update package-name`
- Verify in `poetry.lock` that lock file has updated to fixed version

**Strategy B: Transitive Dependency Fix**
- Identify the parent package bringing in vulnerable version
- Upgrade parent package to one with updated dependencies
- This automatically pulls in the fixed transitive dependency


### 4. Dockerfile Patches

For system-level vulnerabilities (non-Python packages):

**Strategy A: Upgrade Base Image**
- Check if newer Python 3.11-slim image includes fixes
- Update FROM statement: `FROM python:3.11-slim` → newer version

**Strategy B: Explicit Package Installation**
- Add specific package upgrade in RUN commands
- Example: `apt-get install -y libssl3` for OpenSSL CVEs

**Strategy C: Apply Patches**
- Use patching tools for targeted fixes in builder stage
- Document with comments explaining which CVEs are fixed

### 5. Validation Checklist

✓ **CVE Verification**
- Run `docker scout cves` again on patched image
- Confirm target CVE no longer appears
- Note any remaining high/critical issues for tracking

✓ **Build Verification**
```bash
# Build the Docker image
docker build -t robusta:test .

# Verify build succeeds with no errors
echo "Build successful"
```

✓ **Functional Testing**
```bash
# Run basic smoke tests
pytest tests/ -v
```

✓ **Dependency Check**
```bash
# Verify no new vulnerabilities introduced
docker scout cves robusta:test --no-cache

# Validate pyproject.toml metadata and lockfile consistency
poetry check --lock
```

### 6. Documentation

Update these files with CVE fix details:

**Dockerfile Comments:**
```dockerfile
# Patching CVE-XXXX-XXXXX (Critical): Package X
RUN apt-get install -y package-name
```

## Key Considerations

### Python Package CVEs
- Check if vulnerability is in the installed wheel vs source
- For indirect dependencies, finding the transitive source is critical
- Use `poetry why package-name` to understand dependency relationships
- Go version matters for Go-based Python bindings (e.g., Cryptography)

### System Library CVEs
- libexpat1, libssl, libc vulnerabilities are common
- These often have fixes in newer base images
- When possible, upgrade the base Python image before manual fixes

### Testing Strategy
- Always rebuild and scan after each patch
- One CVE at a time is safer; group similar fixes together
- Document any CVEs that can't be patched with reasoning

### Breaking Changes
- Verify patched versions don't introduce breaking changes
- Check release notes and migration guides
- Run full test suite, not just smoke tests for major upgrades

## Implementation Notes

1. Work through CVEs in severity order (Critical → High → Medium)
2. For each CVE, follow the complete cycle: identify → research → patch → validate
3. Commit each logical group of fixes separately
4. Keep diagnostics available: `docker scout cves` output, dependency trees, test results
5. If a patch can't be safely applied, document why in the code comments

## Common Issues and Solutions

### Issue: Patch introduces breaking changes
**Solution:**
1. Check if breaking change is in major version bump
2. Review if dependency needs to be pinned differently
3. Consider if a workaround exists (e.g., compatibility shim)

### Issue: Transitive dependency is vulnerable
**Solution:**
1. Find which package brings it in: `poetry why vulnerable-package`
2. Update the parent package instead
3. Re-lock dependencies and verify fix

### Issue: CVE disappears after unrelated patch
**Solution:**
1. Good sign - often due to transitive dependency updates
2. Still verify with `docker scout cves` on final image
3. Update documentation to credit upstream fixes
