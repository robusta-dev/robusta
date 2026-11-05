#!/bin/bash
# Build CVE-patched Go binaries for the runner Docker image.
#
# kubectl: rebuilt from v1.35.9 source with Go 1.26.9, x/net v0.60.0 and
#   x/text v0.42.0. The official v1.35.9 binary ships Go 1.26.8 / x/net v0.56.0 /
#   x/text v0.39.0 (CVE-2026-56857/78663 Critical, CVE-2026-56866/78659/78660/
#   78667/78669/94439/94440/97031/56851 High). Revert to the official binary once
#   a release has them; check with:
#   go version -m <(curl -sL https://dl.k8s.io/release/<ver>/bin/linux/amd64/kubectl)
#
# Prerequisites: Go 1.21+ installed locally (GOTOOLCHAIN auto-downloads Go 1.26.9)
# Usage: ./scripts/build_go_binaries.sh

set -euo pipefail

export GOTOOLCHAIN=go1.26.9

KUBECTL_VERSION=v1.35.9
X_NET_PATCHED_VERSION=v0.60.0
X_TEXT_PATCHED_VERSION=v0.42.0
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
OUTDIR="$REPO_ROOT/bin/go-cve-rebuild"
TMPDIR=$(mktemp -d)

trap "rm -rf $TMPDIR" EXIT

assert_module_version() {
  local module="$1"
  local expected="$2"
  local actual
  actual="$(go list -m -f '{{if .Replace}}{{.Replace.Version}}{{else}}{{.Version}}{{end}}' "$module" 2>/dev/null)"
  if [ "$actual" != "$expected" ]; then
    echo "ERROR: Expected $module=$expected, got ${actual:-<missing>}" >&2
    exit 1
  fi
}

mkdir -p "$OUTDIR"/{amd64,arm64}

echo "==> Cloning kubernetes $KUBECTL_VERSION (kubectl)..."
git clone --depth 1 --branch "$KUBECTL_VERSION" https://github.com/kubernetes/kubernetes.git "$TMPDIR/kubernetes"
cd "$TMPDIR/kubernetes"

KUBECTL_MAJOR="$(echo "${KUBECTL_VERSION#v}" | cut -d. -f1)"
KUBECTL_MINOR="$(echo "${KUBECTL_VERSION#v}" | cut -d. -f2)"
KUBECTL_LDFLAGS="-w -s \
  -X k8s.io/component-base/version.gitVersion=$KUBECTL_VERSION \
  -X k8s.io/component-base/version.gitMajor=$KUBECTL_MAJOR \
  -X k8s.io/component-base/version.gitMinor=$KUBECTL_MINOR \
  -X k8s.io/component-base/version.gitTreeState=clean"

# go.work ignores go.mod replaces; GOWORK=off honors them.
export GOWORK=off
go mod edit -replace="golang.org/x/net=golang.org/x/net@$X_NET_PATCHED_VERSION"
go mod edit -replace="golang.org/x/text=golang.org/x/text@$X_TEXT_PATCHED_VERSION"
GOFLAGS=-mod=mod assert_module_version "golang.org/x/net" "$X_NET_PATCHED_VERSION"
GOFLAGS=-mod=mod assert_module_version "golang.org/x/text" "$X_TEXT_PATCHED_VERSION"

for arch in amd64 arm64; do
  echo "==> Building kubectl for linux/$arch..."
  CGO_ENABLED=0 GOOS=linux GOARCH=$arch GOFLAGS=-mod=mod go build \
    -ldflags "$KUBECTL_LDFLAGS" \
    -o "$OUTDIR/$arch/kubectl" ./cmd/kubectl
  gzip -f "$OUTDIR/$arch/kubectl"
  (cd "$OUTDIR/$arch" && shasum -a 256 kubectl.gz > kubectl.gz.sha256)
done

ls -lh "$OUTDIR"/*/
