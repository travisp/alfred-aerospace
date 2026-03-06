#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKFLOW_DIR="$ROOT_DIR/workflow"
DEFAULT_OUTPUT="$WORKFLOW_DIR/AeroSpace.alfredworkflow"
OUTPUT_PATH="${1:-$DEFAULT_OUTPUT}"

if [[ ! -f "$WORKFLOW_DIR/info.plist" ]]; then
  echo "Missing workflow/info.plist" >&2
  exit 1
fi

if [[ ! -f "$WORKFLOW_DIR/icon.png" ]]; then
  echo "Missing workflow/icon.png" >&2
  exit 1
fi

TMP_DIR="$(mktemp -d)"
TMP_ARCHIVE="$TMP_DIR/AeroSpace.alfredworkflow"

cleanup() {
  rm -rf "$TMP_DIR"
}

trap cleanup EXIT

mkdir -p "$(dirname "$OUTPUT_PATH")"
chmod +x "$WORKFLOW_DIR"/scripts/*.py

(
  cd "$WORKFLOW_DIR"
  zip -X -r "$TMP_ARCHIVE" \
    info.plist \
    icon.png \
    scripts \
    -x '*/__pycache__/*' \
    -x '*.pyc' \
    -x '*.DS_Store' \
    >/dev/null
)

mv "$TMP_ARCHIVE" "$OUTPUT_PATH"
echo "Built $OUTPUT_PATH"
