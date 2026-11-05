#!/usr/bin/env bash
# Sets the holmes dependency version in helm/robusta/Chart.yaml of the current checkout.
# Run `helm dependency update helm/robusta` afterwards to refresh Chart.lock and charts/.
# usage: helm/set_holmes_version.sh <holmes_version>
set -euo pipefail

HOLMES_VERSION="${1:?holmes version required}"
cd "$(git rev-parse --show-toplevel)"
chart=helm/robusta/Chart.yaml

# the version line directly follows "- name: holmes" in the dependencies list
sed -i -E "/^  - name: holmes\$/{n;s/^(    version: ).*/\1$HOLMES_VERSION/}" "$chart"
grep -A1 -E '^  - name: holmes$' "$chart" | grep -qx "    version: $HOLMES_VERSION" \
  || { echo "failed to set the holmes version in $chart" >&2; exit 1; }
