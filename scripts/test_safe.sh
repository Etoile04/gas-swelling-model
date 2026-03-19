#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ -x "${ROOT_DIR}/.venv/bin/python" ]]; then
  exec "${ROOT_DIR}/.venv/bin/python" "${ROOT_DIR}/scripts/test_safe.py" "$@"
elif [[ -x "${ROOT_DIR}/.venv/Scripts/python.exe" ]]; then
  exec "${ROOT_DIR}/.venv/Scripts/python.exe" "${ROOT_DIR}/scripts/test_safe.py" "$@"
elif command -v python >/dev/null 2>&1; then
  exec "$(command -v python)" "${ROOT_DIR}/scripts/test_safe.py" "$@"
else
  echo "error: no usable python interpreter found" >&2
  exit 1
fi
