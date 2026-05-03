#!/usr/bin/env bash
set -euo pipefail
ENV_FILE="$(cd "$(dirname "$0")/.." && pwd)/.release-versions.env"
echo "Checking .release-versions.env..."
test -f "$ENV_FILE" || { echo "MISSING: $ENV_FILE"; exit 1; }
for key in AUREKAI_VERSION AKAI_PACKAGE_VERSION AUREKAI_MANIFEST_SCHEMA HELM_CHART_VERSION; do
  if grep -q "^${key}=" "$ENV_FILE"; then
    echo "  v $key"
  else
    echo "  x $key missing"; exit 1
  fi
done
echo; echo "All schema checks passed."
