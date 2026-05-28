#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
. "${SCRIPT_DIR}/lib.sh"

ce_load_config
ce_create_runtime_dirs

PYTHON_BIN="${CE_ROOT}/.venv/bin/python"
if [ ! -x "${PYTHON_BIN}" ]; then
  PYTHON_BIN="python3"
fi

exec "${PYTHON_BIN}" "${CE_ROOT}/scripts/refs_tool.py" \
  --repo-root "${CE_ROOT}" \
  --references-root "${CE_REFERENCES_ROOT}" \
  "$@"
