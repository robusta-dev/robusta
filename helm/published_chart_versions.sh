#!/usr/bin/env bash
# Prints every published robusta/robusta chart version, one per line.
# Leaves the "robusta" helm repo added and up to date.
set -euo pipefail

CHART_REPO="${CHART_REPO:-https://robusta-charts.storage.googleapis.com}"
helm repo add --force-update robusta "$CHART_REPO" >/dev/null
helm repo update robusta >/dev/null
helm search repo robusta/robusta --versions --devel -o json \
  | jq -r '.[] | select(.name == "robusta/robusta") | .version'
