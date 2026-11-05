#!/usr/bin/env bash
# Stamps release versions over the placeholders in the checkout:
#   runner version -> 0.0.0 (runner code, pyproject, Chart.yaml appVersion, runner image tag)
#   chart version  -> 0.0.1 (Chart.yaml version)
# A runner release passes the same version twice. holmes-bump.yaml passes a new chart patch
# version with the runner version of an image that has already been published.
# usage: helm/stamp_versions.sh <chart_version> <runner_version>
set -euo pipefail

CHART_VERSION="${1:?chart version required}"
RUNNER_VERSION="${2:?runner version required}"
# run from the root of the checkout to stamp (holmes-bump.yaml runs this copy on an older tag)
cd "$(git rev-parse --show-toplevel)"

sed -i "s/0.0.0/$RUNNER_VERSION/g" src/robusta/_version.py helm/robusta/Chart.yaml helm/robusta/values.yaml
sed -i "s/version = \"0.0.0\"/version = \"$RUNNER_VERSION\"/g" pyproject.toml
sed -i "s/0.0.1/$CHART_VERSION/g" helm/robusta/Chart.yaml
